// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
import CryptoKit
import Darwin

// Portable archive independent of the originating Mac's vault and Keychain.
enum DossierTransfer {
    static let header = Data("TTDOSSIER1".utf8)
    static let maxBytes = 64 * 1024 * 1024
    static func failure(_ code: String) -> NSError {
        NSError(domain: "DossierTransfer", code: 1, userInfo: [NSLocalizedDescriptionKey: code])
    }
    static func encrypt(_ payload: Data, password: String, store: ProfileStore) throws -> Data {
        guard password.count >= 12, password.utf8.count <= 1024 else {throw failure("TRANSFER_PASSWORD")}
        guard payload.count < maxBytes - 128 else {throw failure("TRANSFER_SIZE")}
        let salt = try store.random(32)
        let key = try store.derive(password, salt, 600_000)
        let encrypted = try AES.GCM.seal(payload, using: key, authenticating: header + salt)
        guard let box = encrypted.combined else {throw failure("INVALID_TRANSFER")}
        return header + salt + box
    }
    static func decrypt(_ bytes: Data, password: String, store: ProfileStore) throws -> Data {
        let prefix = header.count + 32
        guard bytes.count < maxBytes, bytes.starts(with: header), bytes.count >= prefix + 28 else {throw failure("INVALID_TRANSFER")}
        guard !password.isEmpty, password.utf8.count <= 1024 else {throw failure("TRANSFER_DECRYPT")}
        let salt = bytes.subdata(in: header.count..<prefix)
        let key = try store.derive(password, salt, 600_000)
        do {
            return try AES.GCM.open(AES.GCM.SealedBox(combined: bytes.dropFirst(prefix)), using: key, authenticating: header + salt)
        } catch {throw failure("TRANSFER_DECRYPT")}
    }
    // This digest covers the encrypted file as well as legacy, unencrypted storage.
    static func revision(_ url: URL) throws -> String {
        guard FileManager.default.fileExists(atPath: url.path) else {return "empty"}
        return SHA256.hash(data: try Data(contentsOf: url)).map{String(format:"%02x",$0)}.joined()
    }
}

struct ResearchImportStorage {
    let dossier: URL
    let archive: URL
    let read: (URL) throws -> Data
    let write: (Data, URL) throws -> Void
    var journal: URL {dossier.appendingPathExtension("import-pending")}

    private func dictionary(_ data: Data) throws -> [String:Any] {
        guard let object = try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw DossierTransfer.failure("INVALID_TRANSFER")}
        return object
    }
    private func entries(_ packet: [String:Any]) throws -> (Data,[(URL,Data)]) {
        guard let desk = packet["dossier"] as? [String:Any], desk["format"] as? String == "tickertwister-research",
              desk["version"] as? Int == 1, let entries = desk["entries"] as? [[String:Any]], entries.count <= 30,
              let records = packet["archive"] as? [[String:Any]] else {throw DossierTransfer.failure("INVALID_TRANSFER")}
        let deskBytes = try JSONSerialization.data(withJSONObject: desk)
        guard deskBytes.count < 5_000_000 else {throw DossierTransfer.failure("TRANSFER_SIZE")}
        var ids = Set<String>(), additions = [(URL,Data)]()
        for record in records {
            guard let id=record["id"] as? String, ProfileStore.isValidID(id), ids.insert(id.lowercased()).inserted,
                  let input=record["input"] as? [String:Any], let companies=input["companies"] as? [[String:Any]],
                  (1...4).contains(companies.count), let language=record["language"] as? String,
                  ["en","nl","fr","de","es","it","pt"].contains(language),
                  let result=record["response"] as? [String:Any], result["status"] as? String=="completed" else {throw DossierTransfer.failure("INVALID_TRANSFER")}
            let raw = try JSONSerialization.data(withJSONObject: record)
            guard raw.count < 250_000 else {throw DossierTransfer.failure("TRANSFER_SIZE")}
            let url=archive.appendingPathComponent(id+".json")
            if FileManager.default.fileExists(atPath:url.path) {
                let existing = try dictionary(read(url))
                // Old archives may omit nullable settings or translationOf.
                var comparable=existing
                for k in ["settings","translationOf"] where comparable[k] == nil {comparable[k]=NSNull()}
                var incoming=record
                for k in ["settings","translationOf"] where incoming[k] == nil {incoming[k]=NSNull()}
                guard NSDictionary(dictionary: comparable).isEqual(to: incoming) else {throw DossierTransfer.failure("TRANSFER_CONFLICT")}
            } else {additions.append((url,raw))}
        }
        return (deskBytes,additions)
    }

    // New records are additive. The atomic dossier write is last. A durable, private
    // journal completes the same transaction after interruption without overwriting AI records.
    func apply(_ payload: Data, expectedRevision: String) throws {
        try locked {
            try recoverLocked()
            guard try DossierTransfer.revision(dossier)==expectedRevision else {throw DossierTransfer.failure("DOSSIER_CHANGED")}
            guard payload.count<DossierTransfer.maxBytes else {throw DossierTransfer.failure("TRANSFER_SIZE")}
            var packet=try dictionary(payload)
            let work = try entries(packet)
            if FileManager.default.fileExists(atPath:dossier.path) {
                let backup=dossier.appendingPathExtension("backup")
                try Data(contentsOf:dossier).write(to:backup,options:.atomic)
                try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:backup.path)
            }
            packet["baseRevision"]=expectedRevision
            try write(JSONSerialization.data(withJSONObject:packet),journal)
            try finish(work,base:expectedRevision)
        }
    }
    func recover() throws {try locked {try recoverLocked()}}
    private func recoverLocked() throws {
        if FileManager.default.fileExists(atPath:journal.path) {
            let packet=try dictionary(read(journal))
            guard let base=packet["baseRevision"] as? String else {throw DossierTransfer.failure("INVALID_TRANSFER")}
            do {try finish(entries(packet),base:base)}
            catch let error as NSError where error.domain=="DossierTransfer" && ["DOSSIER_CHANGED","TRANSFER_CONFLICT"].contains(error.localizedDescription) {
                // Another copy of the app edited a destination during the interruption.
                // Preserve those edits and allow the original transfer file to be retried.
                try FileManager.default.removeItem(at:journal)
                throw error
            }
        }
    }
    private func locked(_ operation: () throws -> Void) throws {
        let lockfile=dossier.appendingPathExtension("transfer-lock")
        let fd=Darwin.open(lockfile.path,O_RDWR | O_CREAT | O_CLOEXEC | O_NOFOLLOW,0o600)
        guard fd>=0 else {throw POSIXError(.EIO)}
        defer {Darwin.close(fd)}
        guard flock(fd,LOCK_EX)==0 else {throw POSIXError(.EIO)}
        try operation()
    }
    private func finish(_ work: (Data,[(URL,Data)]),base:String) throws {
        let changed=try DossierTransfer.revision(dossier) != base
        if changed {
            // We might have committed the dossier just before an interruption. Never
            // overwrite edits made in a different preview during recovery.
            guard FileManager.default.fileExists(atPath:dossier.path),
                  try NSDictionary(dictionary:dictionary(read(dossier))).isEqual(to:dictionary(work.0)) else {
                throw DossierTransfer.failure("DOSSIER_CHANGED")
            }
        }
        for (url,data) in work.1 {try write(data,url)}
        if !changed {try write(work.0,dossier)}
        try FileManager.default.removeItem(at:journal)
    }
}
