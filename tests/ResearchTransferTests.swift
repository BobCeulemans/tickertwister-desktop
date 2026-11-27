// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
@main enum ResearchTransferTests {
    static func requireFailure(_ call: () throws -> Void) {
        do {try call(); fatalError("Operation unexpectedly succeeded")} catch {}
    }
    static func main() throws {
        let fs=FileManager.default, root=fs.temporaryDirectory.appendingPathComponent("tt-transfer-test-"+UUID().uuidString)
        defer {try? fs.removeItem(at:root)}
        let sender=ProfileStore(root:root.appendingPathComponent("Sender"),removeAccountKey:{_ in})
        let receiver=ProfileStore(root:root.appendingPathComponent("Receiver"),removeAccountKey:{_ in})
        try sender.create("Sender","Example-ACCOUNT-1")
        try receiver.create("Recipient","Example-ACCOUNT-2")
        let dossier=try receiver.privateURL("research.json"),archive=try receiver.privateURL("research.ai-archive")
        let desk:[String:Any]=["format":"tickertwister-research","version":1,"entries":[["test":"Private thesis"]]]
        let record:[String:Any]=["id":UUID().uuidString,"input":["companies":[["symbol":"TEST"]]],"language":"nl","response":["status":"completed"]]
        let body=try JSONSerialization.data(withJSONObject:["dossier":desk,"archive":[record]])
        let password="Independent-transfer-password"
        let encrypted=try DossierTransfer.encrypt(body,password:password,store:sender)
        assert(encrypted.range(of:Data("Private thesis".utf8))==nil)
        let decoded=try DossierTransfer.decrypt(encrypted,password:password,store:receiver)
        assert(decoded==body)
        requireFailure {_ = try DossierTransfer.decrypt(encrypted,password:"wrong",store:receiver)}
        var corrupt=encrypted;corrupt[corrupt.count-1] ^= 1
        requireFailure {_ = try DossierTransfer.decrypt(corrupt,password:password,store:receiver)}
        requireFailure {_ = try DossierTransfer.encrypt(body,password:"too short",store:sender)}
        let destination=archive.appendingPathComponent((record["id"] as! String)+".json")
        var abort=true
        let storage=ResearchImportStorage(dossier:dossier,archive:archive,read:receiver.read,write:{data,url in
            if url==dossier && abort {abort=false;throw CocoaError(.fileWriteOutOfSpace)}
            try receiver.write(data,to:url)
        })
        requireFailure {try storage.apply(body,expectedRevision:"empty")}
        assert(fs.fileExists(atPath:storage.journal.path) && fs.fileExists(atPath:destination.path) && !fs.fileExists(atPath:dossier.path))
        let staged=try Data(contentsOf:storage.journal);assert(staged.starts(with:ProfileStore.magic))
        try storage.recover()
        let imported=try JSONSerialization.jsonObject(with:receiver.read(dossier)) as! NSDictionary
        precondition(imported.isEqual(to:desk));assert(!fs.fileExists(atPath:storage.journal.path))
        let savedRecord=try Data(contentsOf:destination)
        let revision=try DossierTransfer.revision(dossier)
        try storage.apply(body,expectedRevision:revision)
        let newRecord=try Data(contentsOf:destination);assert(newRecord==savedRecord)
        requireFailure {try storage.apply(body,expectedRevision:"empty")}
        var conflict=record;conflict["language"]="fr"
        let different=try JSONSerialization.data(withJSONObject:["dossier":desk,"archive":[conflict]])
        requireFailure {try storage.apply(different,expectedRevision:DossierTransfer.revision(dossier))}
        assert(!fs.fileExists(atPath:storage.journal.path))
        print("PASS: independent transfer password, cross-account decryption, wrong password, tamper, encrypted journal, interruption recovery, idempotence, stale revision and conflicting archive protection")
    }
}
