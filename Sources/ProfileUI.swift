// SPDX-License-Identifier: AGPL-3.0-only
import AppKit

extension AppDelegate {
    func profileStatus() throws -> [String:Any] {
        let list=usesProfiles ? try profiles.accounts():[]
        return ["accounts":list.map{["id":$0.id,"name":$0.name]},"active":profiles.active.map{["id":$0.id,"name":$0.name]} as Any? ?? NSNull(),"testing":testing && !profileTesting]
    }
    func readPrivate(_ url:URL) throws -> Data {try profiles.active != nil && usesProfiles ? profiles.read(url):Data(contentsOf:url)}
    func writePrivate(_ data:Data,to url:URL) throws {
        if profiles.active != nil && usesProfiles {try profiles.write(data,to:url)}else{try data.write(to:url,options:.atomic);try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:url.path)}
    }
    func profileAction(_ action:String,_ body:[String:Any],_ id:Int){
        let language=body["language"] as? String ?? Localization.current
        func text(_ a:String,_ b:String)->String{Localization.text(b,language)}
        do {
            if action=="profile-status" {reply(id,true,try profileStatus());return}
            guard !aiBusy,engineProcesses.isEmpty,printView==nil else{throw profiles.failure(text("Wacht tot de lopende analyse of afdruk klaar is.","Wait for the current analysis or print job to finish."))}
            guard !researchDirty else{throw profiles.failure(text("Bewaar eerst je dossierwijzigingen.","Save your dossier changes first."))}
            if action=="profile-lock" {
                aiKey=nil;profiles.lock();pendingOpen=nil
                reply(id,true,["done":true]);webView.reload();return
            }
            let alert=NSAlert()
            let creating=action=="profile-create",changing=action=="profile-password"
            guard creating || changing || action=="profile-login" else{throw profiles.failure("INVALID_PROFILE_ACTION")}
            if creating {guard profiles.active==nil else{throw profiles.failure(text("Vergrendel eerst het huidige account.","Lock the current account first."))}}
            if changing {guard profiles.active != nil else{throw profiles.failure("PROFILE_LOCKED")}}
            alert.messageText=text(creating ? "Lokaal account maken":changing ? "Wachtwoord wijzigen":"Account ontgrendelen",creating ? "Create local account":changing ? "Change password":"Unlock account")
            alert.informativeText=text("Alleen op deze Mac. Het wachtwoord vergrendelt je versleutelde dossier en API-sleutel. Geen e-mail, cloudaccount of wachtwoordherstel. Bewaar je wachtwoord veilig. Minimaal 12 tekens. Voor dit lokale account is geen website-URL nodig. Een eventuele URL-vraag komt van je wachtwoordbeheerder.","Only on this Mac. The password locks your encrypted dossier and API key. No email, cloud account or password recovery. Keep your password safe. At least 12 characters. This local account needs no website URL. Any URL prompt comes from your password manager.")
            let view=NSView(frame:NSRect(x:0,y:0,width:440,height:creating ? 160:changing ? 110:40))
            let name=NSTextField(frame:NSRect(x:0,y:125,width:440,height:26));name.placeholderString=text("Gebruikersnaam","Username")
            let password=NSSecureTextField(frame:NSRect(x:0,y:creating ? 87:changing ? 74:6,width:440,height:26));password.placeholderString=text(changing ? "Huidig wachtwoord":"Wachtwoord",changing ? "Current password":"Password")
            let confirm=NSSecureTextField(frame:NSRect(x:0,y:creating ? 49:40,width:440,height:26));confirm.placeholderString=text(changing ? "Nieuw wachtwoord":"Herhaal wachtwoord",changing ? "New password":"Repeat password")
            let repeatNew=NSSecureTextField(frame:NSRect(x:0,y:6,width:440,height:26));repeatNew.placeholderString=text("Herhaal nieuw wachtwoord","Repeat new password")
            let takeLegacy=NSButton(checkboxWithTitle:text("Neem mijn bestaande dossier en AI-archief over","Import my existing dossier and AI archive"),target:nil,action:nil);takeLegacy.frame=NSRect(x:0,y:8,width:440,height:26)
            let first=try profiles.accounts().isEmpty
            if creating {view.addSubview(name);view.addSubview(confirm);if first{takeLegacy.state = .on;view.addSubview(takeLegacy)}}
            if changing {view.addSubview(confirm);view.addSubview(repeatNew)}
            view.addSubview(password);alert.accessoryView=view
            alert.addButton(withTitle:text(creating ? "Maak account":changing ? "Wijzig wachtwoord":"Ontgrendel",creating ? "Create account":changing ? "Change password":"Unlock"));alert.addButton(withTitle:text("Annuleer","Cancel"))
            alert.window.initialFirstResponder=creating ? name:password
            guard alert.runModal()==NSApplication.ModalResponse.alertFirstButtonReturn else {reply(id,true,["cancelled":true]);return}
            defer {password.stringValue="";confirm.stringValue="";repeatNew.stringValue=""}
            if creating {
                guard password.stringValue==confirm.stringValue else{throw profiles.failure(text("Wachtwoorden verschillen.","Passwords do not match."))}
                var files=[(URL,String)]()
                if first && takeLegacy.state == .on {
                    let base=profiles.root.deletingLastPathComponent(),research=base.appendingPathComponent("research.json"),archive=base.appendingPathComponent("research.ai-archive")
                    if FileManager.default.fileExists(atPath:research.path){files.append((research,"research.json"))}
                    if FileManager.default.fileExists(atPath:archive.path){for url in try FileManager.default.contentsOfDirectory(at:archive,includingPropertiesForKeys:nil) where url.pathExtension=="json" {files.append((url,"research.ai-archive/"+url.lastPathComponent))}}
                }
                try profiles.create(name.stringValue,password.stringValue,legacyFiles:files)
                if !files.isEmpty {
                    let note=NSAlert();note.messageText=text("Bestaande gegevens veilig gekopieerd","Existing data copied safely")
                    note.informativeText=text("De nieuwe accountkopie is versleuteld en gecontroleerd. Je oorspronkelijke dossier en AI-archief blijven als onversleutelde reservekopie in Application Support/Tickertwister staan. Ook eerder geëxporteerde analyses en PDF’s blijven onversleuteld. Verwijder oude kopieën zelf pas nadat je de overname hebt gecontroleerd.","The new account copy is encrypted and verified. The original dossier and AI archive remain as unencrypted backups in Application Support/Tickertwister. Previously exported analyses and PDFs also remain unencrypted. Remove old copies yourself only after checking the import.");note.runModal()
                }
            }else if changing {
                guard let account=profiles.active,confirm.stringValue==repeatNew.stringValue else{throw profiles.failure(text("Wachtwoorden verschillen.","Passwords do not match."))}
                try profiles.login(account.id,password.stringValue)
                try profiles.changePassword(confirm.stringValue)
            }else{
                guard let account=body["account"] as? String else{throw profiles.failure("LOGIN_FAILED")}
                try profiles.login(account,password.stringValue)
            }
            aiKey=nil;researchDirty=false
            reply(id,true,["done":true]);webView.reload()
        }catch{reply(id,false,["error":error.localizedDescription])}
    }
}
