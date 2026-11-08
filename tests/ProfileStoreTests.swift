// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
@main struct ProfileStoreTests {
 static func check(_ value: @autoclosure () throws -> Bool) throws { let result=try value();precondition(result) }
 static func main() throws {
  let root=URL(fileURLWithPath:NSTemporaryDirectory()).appendingPathComponent("tt-profile-tests-"+UUID().uuidString)
  defer{try? FileManager.default.removeItem(at:root)}
  let store=ProfileStore(root:root.appendingPathComponent("Profiles"))
  try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
  let legacy=root.appendingPathComponent("legacy.json"),original=Data("{\"notes\":\"PRIVATE TEST NOTE\"}".utf8)
  try original.write(to:legacy)
  try store.create("Alice","correct horse battery staple",legacyFiles:[(legacy,"research.json")])
  let alice=store.active!,aliceFile=try store.privateURL("research.json")
  try check(store.read(aliceFile)==original)
  let disk=try Data(contentsOf:aliceFile)
  precondition(disk.starts(with:ProfileStore.magic));precondition(!String(decoding:disk,as:UTF8.self).contains("PRIVATE TEST NOTE"))
  try check(Data(contentsOf:legacy)==original)
  let encryptedSecret=try store.seal(Data("TEST-API-SECRET".utf8),context:"api")
  store.lock()
  do{_ = try store.read(aliceFile);fatalError("locked vault readable")}catch{}
  do{try store.login(alice.id,"wrong password");fatalError("wrong password accepted")}catch{}
  // A fresh instance simulates restarting; PBKDF2 remains the offline protection.
  let fresh=ProfileStore(root:store.root)
  try fresh.login(alice.id,"correct horse battery staple")
  try check(fresh.read(aliceFile)==original)
  try fresh.changePassword("a new strong test password")
  fresh.lock()
  do{try fresh.login(alice.id,"correct horse battery staple");fatalError("old password accepted")}catch{}
  let changed=ProfileStore(root:store.root)
  try changed.login(alice.id,"a new strong test password")
  try check(changed.unseal(encryptedSecret,context:"api")==Data("TEST-API-SECRET".utf8))
  changed.lock();try changed.create("Bob","second strong test password")
  let emptyPath=try changed.privateURL("research.json").path;precondition(!FileManager.default.fileExists(atPath:emptyPath))
  do{_ = try changed.read(aliceFile);fatalError("cross-profile read accepted")}catch{}
  do{_ = try changed.unseal(encryptedSecret,context:"api");fatalError("cross-profile secret accepted")}catch{}
  changed.lock();try changed.login(alice.id,"a new strong test password")
  var tampered=disk;tampered[tampered.count-1] ^= 1
  try tampered.write(to:aliceFile)
  do{_ = try changed.read(aliceFile);fatalError("tampered ciphertext accepted")}catch{}
  try disk.write(to:aliceFile)
  do{_ = try changed.unseal(encryptedSecret,context:"other");fatalError("wrong context accepted")}catch{}
  do{try changed.create("Alice","another long password");fatalError("duplicate user accepted")}catch{}
  let previous=changed.active!.id
  do{try changed.create("Failure","another long password",legacyFiles:[(root.appendingPathComponent("missing"),"research.json")]);fatalError("bad migration accepted")}catch{}
  precondition(changed.active?.id==previous);try check(changed.accounts().count==2)
  let index=try String(contentsOf:store.index,encoding:.utf8)
  precondition(!index.contains("password"));precondition(!index.contains("TEST-API-SECRET"))
  // Optional isolated Keychain integration. Only this random account item is touched.
  if CommandLine.arguments.contains("--keychain") {
   try changed.saveAPIKey("sk-test-not-a-real-api-key")
   try check(changed.loadAPIKey()=="sk-test-not-a-real-api-key")
   try changed.forgetAPIKey();try check(changed.loadAPIKey()==nil)
  }
  print("PASS: encryption, locked access, wrong password, relaunch, password change, profile isolation, tamper detection, associated context, atomic migration rollback, legacy preservation" )
 }
}
