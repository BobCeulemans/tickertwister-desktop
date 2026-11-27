// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import Foundation
import Darwin
import CryptoKit
import Security
import CommonCrypto

// No passwords or unwrapped encryption keys are persisted. Account metadata is public;
// each random vault key is wrapped by a PBKDF2-derived key using authenticated AES-GCM.
final class ProfileStore {
    struct Account: Codable {
        let id: String
        var name: String
        var salt: Data
        var wrappedKey: Data
        var rounds: UInt32
    }
    let root: URL
    private(set) var active: Account?
    private var key: SymmetricKey?
    private var attempts=0
    private var nextAttempt=Date.distantPast
    static let magic=Data("TTVAULT1".utf8)
    private let removeAccountKey: (String) throws -> Void
    init(root: URL, removeAccountKey: @escaping (String) throws -> Void = ProfileStore.deleteKeychainItem) {
        self.root = root
        self.removeAccountKey = removeAccountKey
        recoverInterruptedRemovals()
    }
    var index: URL { root.appendingPathComponent("accounts.json") }
    static func isValidID(_ value:String) -> Bool {
        // Foundation may accept a UUID prefix before a NUL. Require the entire
        // identifier to match its canonical spelling before using it in a path.
        guard value.utf8.count==36,let id=UUID(uuidString:value) else{return false}
        return id.uuidString.lowercased()==value.lowercased()
    }
    func accounts() throws -> [Account] {
        guard FileManager.default.fileExists(atPath:index.path) else { return [] }
        let data=try Data(contentsOf:index)
        guard data.count<100000 else { throw failure("ACCOUNT_INDEX_INVALID") }
        let accounts=try JSONDecoder().decode([Account].self,from:data)
        guard accounts.count<=30,Set(accounts.map(\.id)).count==accounts.count,
              accounts.allSatisfy({Self.isValidID($0.id) && $0.salt.count==32 && $0.rounds==600000}) else {throw failure("ACCOUNT_INDEX_INVALID")}
        return accounts
    }
    func failure(_ message:String)->NSError { NSError(domain:"Profile",code:1,userInfo:[NSLocalizedDescriptionKey:message]) }
    func directory(_ account:Account)->URL {root.appendingPathComponent(account.id,isDirectory:true)}
    func privateURL(_ filename:String) throws -> URL {
        guard let active=active,key != nil else {throw failure("PROFILE_LOCKED")}
        return directory(active).appendingPathComponent(filename)
    }
    func derive(_ password:String,_ salt:Data,_ rounds:UInt32) throws -> SymmetricKey {
        let bytes=Array(password.utf8);var output=[UInt8](repeating:0,count:32)
        let status=bytes.withUnsafeBytes { pass in salt.withUnsafeBytes { s in
            CCKeyDerivationPBKDF(CCPBKDFAlgorithm(kCCPBKDF2),pass.baseAddress!.assumingMemoryBound(to:CChar.self),bytes.count,s.baseAddress!.assumingMemoryBound(to:UInt8.self),salt.count,CCPseudoRandomAlgorithm(kCCPRFHmacAlgSHA256),rounds,&output,output.count)
        }}
        guard status==kCCSuccess else {throw failure("KEY_DERIVATION_FAILED")}
        defer {_ = output.withUnsafeMutableBytes{ $0.initializeMemory(as:UInt8.self,repeating:0) }}
        return SymmetricKey(data:output)
    }
    func random(_ count:Int) throws -> Data {var bytes=[UInt8](repeating:0,count:count);guard SecRandomCopyBytes(kSecRandomDefault,count,&bytes)==errSecSuccess else{throw failure("RANDOM_FAILED")};return Data(bytes)}
    func makeAccount(_ name:String,_ password:String) throws -> (Account,SymmetricKey) {
        let name=name.trimmingCharacters(in:.whitespacesAndNewlines)
        guard (2...40).contains(name.count),!name.unicodeScalars.contains(where:CharacterSet.controlCharacters.contains),password.count>=12,password.utf8.count<=1024 else {throw failure("USE_NAME_AND_12_CHARACTER_PASSWORD")}
        let salt=try random(32),id=UUID().uuidString,key=SymmetricKey(size:.bits256)
        let derived=try derive(password,salt,600000)
        let wrapped=try AES.GCM.seal(key.withUnsafeBytes{Data($0)},using:derived,authenticating:Data(id.utf8)).combined!
        return (Account(id:id,name:name,salt:salt,wrappedKey:wrapped,rounds:600000),key)
    }
    // Different preview bundles can share this profile directory. Serialize changes to the index
    // and recovery so a second launch cannot restore a vault while the first launch is deleting it.
    private func withIndexLock(_ operation: () throws -> Void) throws {
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        let lockFile = root.appendingPathComponent(".accounts.lock")
        let descriptor = Darwin.open(lockFile.path, O_RDWR | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0o600)
        guard descriptor >= 0 else { throw failure("ACCOUNT_INDEX_WRITE_FAILED") }
        defer { Darwin.close(descriptor) }
        guard flock(descriptor, LOCK_EX) == 0 else { throw failure("ACCOUNT_INDEX_WRITE_FAILED") }
        try operation()
    }

    func create(_ name:String,_ password:String,legacyFiles:[(URL,String)]=[]) throws {
        try withIndexLock {
            var list=try accounts()
            guard list.count<30,!list.contains(where:{$0.name.caseInsensitiveCompare(name.trimmingCharacters(in:.whitespacesAndNewlines)) == .orderedSame}) else{throw failure("ACCOUNT_EXISTS_OR_LIMIT")}
            let (account,newKey)=try makeAccount(name,password)
            let previous=active,previousKey=key
            try FileManager.default.createDirectory(at:directory(account),withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
            active=account;key=newKey
            do {
                // Copy and verify before committing the account index. Original files remain untouched.
                for (source,relative) in legacyFiles {
                    let data=try Data(contentsOf:source)
                    let destination=directory(account).appendingPathComponent(relative)
                    try write(data,to:destination)
                    guard try read(destination)==data else{throw failure("MIGRATION_VERIFICATION_FAILED")}
                }
                list.append(account)
                try writeIndex(list)
            } catch {active=previous;key=previousKey;try? FileManager.default.removeItem(at:directory(account));throw error}
        }
    }

    func writeIndex(_ list:[Account]) throws {
        try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        // Set permissions before the atomic rename. An error must mean the old index is still in place.
        let temporary = root.appendingPathComponent(".index-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: temporary) }
        let data = try JSONEncoder().encode(list)
        guard FileManager.default.createFile(atPath: temporary.path, contents: data, attributes: [.posixPermissions: 0o600]) else {
            throw failure("ACCOUNT_INDEX_WRITE_FAILED")
        }
        guard Darwin.rename(temporary.path, index.path) == 0 else { throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO) }
    }
    func login(_ id:String,_ password:String) throws {
        guard Date()>=nextAttempt else{throw failure("LOGIN_WAIT")}
        guard !password.isEmpty,password.utf8.count<=1024,let account=try accounts().first(where:{$0.id==id}) else{throw failure("LOGIN_FAILED")}
        do {
            let derived=try derive(password,account.salt,account.rounds)
            let raw=try AES.GCM.open(AES.GCM.SealedBox(combined:account.wrappedKey),using:derived,authenticating:Data(account.id.utf8))
            guard raw.count==32 else{throw failure("LOGIN_FAILED")}
            active=account;key=SymmetricKey(data:raw);attempts=0;nextAttempt = .distantPast
        }catch{attempts+=1;nextAttempt=Date().addingTimeInterval(min(30,Double(attempts*2)));throw failure("LOGIN_FAILED")}
    }
    func changePassword(_ password:String) throws {
        try withIndexLock {
            guard var account=active,let key=key,password.count>=12,password.utf8.count<=1024 else{throw failure("USE_12_CHARACTER_PASSWORD")}
            account.salt=try random(32)
            let derived=try derive(password,account.salt,account.rounds)
            account.wrappedKey=try AES.GCM.seal(key.withUnsafeBytes{Data($0)},using:derived,authenticating:Data(account.id.utf8)).combined!
            let list=try accounts().map{$0.id==account.id ? account:$0}
            try writeIndex(list);active=account
        }
    }

    func renameActive(to proposedName: String, password: String) throws {
        try withIndexLock {
            guard let current = active else { throw failure("PROFILE_LOCKED") }
            try login(current.id, password)
            let name = proposedName.trimmingCharacters(in: .whitespacesAndNewlines)
            guard (2...40).contains(name.count), !name.unicodeScalars.contains(where: CharacterSet.controlCharacters.contains) else {
                throw failure("INVALID_ACCOUNT_NAME")
            }
            var list = try accounts()
            guard let position = list.firstIndex(where: { $0.id == current.id }) else { throw failure("LOGIN_FAILED") }
            guard !list.contains(where: { $0.id != current.id && $0.name.caseInsensitiveCompare(name) == .orderedSame }) else {
                throw failure("ACCOUNT_EXISTS_OR_LIMIT")
            }
            list[position].name = name
            try writeIndex(list)
            active = list[position]
        }
    }

    func deleteActive(password: String) throws {
        try withIndexLock {
            guard let current = active else { throw failure("PROFILE_LOCKED") }
            try login(current.id, password)
            let remaining = try accounts().filter { $0.id != current.id }
            let vault = directory(current)
            let pending = root.appendingPathComponent(".removing-" + current.id, isDirectory: true)
            try FileManager.default.moveItem(at: vault, to: pending)
            do {
                try writeIndex(remaining)
            } catch {
                try FileManager.default.moveItem(at: pending, to: vault)
                throw error
            }
            lock()
            // The account and its wrapped vault key are gone. Keep the pending folder for a retry
            // if the Keychain is locked or the encrypted files cannot be removed at this moment.
            try? finishRemoval(current.id, pending)
        }
    }

    private func finishRemoval(_ id: String, _ pending: URL) throws {
        try removeAccountKey(id)
        try FileManager.default.removeItem(at: pending)
    }

    private func recoverInterruptedRemovals() {
        let manager = FileManager.default
        let prefix = ".removing-"
        guard let names = try? manager.contentsOfDirectory(atPath: root.path),
              names.contains(where: { $0.hasPrefix(prefix) }) else { return }
        try? withIndexLock {
            guard manager.fileExists(atPath: index.path) else { return }
            let list = try accounts()
            for item in try manager.contentsOfDirectory(atPath: root.path) where item.hasPrefix(prefix) {
                let id = String(item.dropFirst(prefix.count))
                guard Self.isValidID(id) else { continue }
                let folder = root.appendingPathComponent(item)
                if let account = list.first(where: { $0.id == id }) {
                    if !manager.fileExists(atPath: directory(account).path) {
                        try? manager.moveItem(at: folder, to: directory(account))
                    }
                } else {
                    try? finishRemoval(id, folder)
                }
            }
        }
    }
    func lock(){key=nil;active=nil}
    func seal(_ data:Data,context:String) throws -> Data {
        guard let key=key,let active=active else{throw failure("PROFILE_LOCKED")}
        return Self.magic + (try AES.GCM.seal(data,using:key,authenticating:Data((active.id+":"+context).utf8)).combined!)
    }
    func unseal(_ data:Data,context:String) throws -> Data {
        guard let key=key,let active=active,data.starts(with:Self.magic) else{throw failure("VAULT_INVALID_OR_LOCKED")}
        return try AES.GCM.open(AES.GCM.SealedBox(combined:data.dropFirst(Self.magic.count)),using:key,authenticating:Data((active.id+":"+context).utf8))
    }
    func write(_ data:Data,to url:URL) throws {
        let sealed=try seal(data,context:url.lastPathComponent)
        try FileManager.default.createDirectory(at:url.deletingLastPathComponent(),withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        try sealed.write(to:url,options:.atomic)
        try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:url.path)
    }
    func read(_ url:URL) throws -> Data {try unseal(Data(contentsOf:url),context:url.lastPathComponent)}
    private static func keychainQuery(_ accountID: String) -> [String:Any] {
        [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"be.bobceulemans.tickertwister.openai.v5",kSecAttrAccount as String:accountID,kSecAttrSynchronizable as String:false]
    }
    private static func deleteKeychainItem(_ accountID: String) throws {
        let status = SecItemDelete(keychainQuery(accountID) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw NSError(domain: "Profile", code: 1, userInfo: [NSLocalizedDescriptionKey:"KEYCHAIN_DELETE_FAILED"])
        }
    }
    func keychainQuery() throws -> [String:Any] {
        guard let active=active,key != nil else{throw failure("PROFILE_LOCKED")}
        return Self.keychainQuery(active.id)
    }
    func saveAPIKey(_ value:String) throws {
        let query=try keychainQuery(),data=try seal(Data(value.utf8),context:"openai-api-key")
        let updated=SecItemUpdate(query as CFDictionary,[kSecValueData as String:data] as CFDictionary)
        if updated==errSecItemNotFound {
            // Native macOS login Keychain, not the entitlement-dependent iOS-style store.
            // Non-synchronizable; the value is additionally encrypted by the account vault.
            var item=query;item[kSecValueData as String]=data
            let status=SecItemAdd(item as CFDictionary,nil)
            guard status==errSecSuccess else{throw failure("KEYCHAIN_SAVE_FAILED (\(status))")}
        }else if updated != errSecSuccess{throw failure("KEYCHAIN_SAVE_FAILED (\(updated))")}
    }
    func loadAPIKey() throws -> String? {
        var query=try keychainQuery();query[kSecReturnData as String]=true;query[kSecMatchLimit as String]=kSecMatchLimitOne
        var result:CFTypeRef?;let status=SecItemCopyMatching(query as CFDictionary,&result)
        if status==errSecItemNotFound{return nil}
        guard status==errSecSuccess,let data=result as? Data,let value=String(data:try unseal(data,context:"openai-api-key"),encoding:.utf8) else{throw failure("KEYCHAIN_READ_FAILED")}
        return value
    }
    func forgetAPIKey() throws {
        guard let active = active, key != nil else { throw failure("PROFILE_LOCKED") }
        try Self.deleteKeychainItem(active.id)
    }
}
