// SPDX-License-Identifier: AGPL-3.0-only
// Isolated native UI regression harness, only --smoke-test ... --profile-test.
import AppKit
import WebKit
private var profilePhase=0
private var profileResults=[String:Any]()
extension AppDelegate {
    func fillTestProfileDialog(_ name:String){
        let timer=Timer(timeInterval:0.15,repeats:true){timer in
            guard let view=NSApp.modalWindow?.contentView else{return}
            func descendants(_ v:NSView)->[NSView]{[v]+v.subviews.flatMap{descendants($0)}}
            let children=descendants(view)
            let secure=children.compactMap{$0 as? NSSecureTextField}
            guard !secure.isEmpty else{return}
            for field in secure {field.stringValue="only-a-test-password-501"}
            for field in children.compactMap({$0 as? NSTextField}) where field.placeholderString=="Gebruikersnaam" || field.placeholderString=="Username" {field.stringValue=name}
            if let button=children.compactMap({$0 as? NSButton}).first(where:{["Maak account","Create account","Ontgrendel","Unlock"].contains($0.title)}) {timer.invalidate();button.performClick(nil)}
        }
        RunLoop.main.add(timer,forMode:.common);RunLoop.main.add(timer,forMode:.modalPanel)
        DispatchQueue.main.asyncAfter(deadline:.now()+12){timer.invalidate()}
    }
    func profileTestScript(_ script:String,_ completion:@escaping(Any)->Void){
        webView.callAsyncJavaScript("const pause=ms=>new Promise(r=>setTimeout(r,ms));"+script,arguments:[:],in:nil,in:.page){result in
            switch result{case .success(let value):completion(value)
            case .failure(let error):self.finishProfileTest(error.localizedDescription)}
        }
    }
    func finishProfileTest(_ error:String?=nil){
        if let error=error{profileResults["error"]=error}
        if let output=testOutput,let data=try? JSONSerialization.data(withJSONObject:profileResults,options:.prettyPrinted){try? data.write(to:URL(fileURLWithPath:output+".profiles.json"))}
        let config=WKSnapshotConfiguration();config.rect=webView.bounds
        webView.takeSnapshot(with:config){image,_ in
            if let output=self.testOutput,let tiff=image?.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]){try? png.write(to:URL(fileURLWithPath:output+".profiles.png"))}
            NSApp.terminate(nil)
        }
    }
    func testProfiles(){
        guard profileTesting else{return}
        let phase=profilePhase;profilePhase+=1
        switch phase {
        case 0:
            profileTestScript("await pause(600);document.querySelector('.profile-button').click();await pause(100);return !!document.querySelector('.profile-overlay');"){value in
                profileResults["accountPanel"]=value;self.fillTestProfileDialog("QA Alice")
                self.webView.evaluateJavaScript("document.querySelector('.profile-overlay .primary').click()",completionHandler:nil)
            }
        case 1:
            profileTestScript("await pause(500);window.dispatchEvent(new CustomEvent('desktop-open-report',{detail:window.__studioFixture}));await pause(200);document.querySelector('[data-action=research-toggle]').click();await pause(150);document.querySelector('[data-action=desk-pin]').click();await pause(150);document.querySelector('.thesis-editor').open=true;const area=document.querySelector('[data-note=thesis]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(area,'PRIVATE PROFILE UI TEST');area.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);document.querySelector('[data-action=thesis-save]').click();await pause(300);return document.querySelector('.profile-button').textContent;"){value in
                profileResults["createdAlice"]=value
                do {
                    let data=try Data(contentsOf:self.profiles.privateURL("research.json"))
                    profileResults["encryptedResearch"]=data.starts(with:ProfileStore.magic) && !String(decoding:data,as:UTF8.self).contains("PRIVATE PROFILE UI TEST")
                    try self.profiles.saveAPIKey("sk-test-not-a-real-key-501")
                    profileResults["keychainSaved"]=true
                }catch{profileResults["keychainOrSaveError"]=error.localizedDescription}
                self.webView.evaluateJavaScript("document.querySelector('.profile-button').click();setTimeout(()=>document.querySelector('.profile-overlay .primary').click(),100)",completionHandler:nil)
            }
        case 2:
            profileTestScript("await pause(500);return !document.querySelector('header') && !!document.querySelector('.profile-overlay');"){value in
                profileResults["lockedHidesApp"]=value;self.fillTestProfileDialog("QA Bob")
                self.webView.evaluateJavaScript("document.querySelector('.profile-overlay .primary').click()",completionHandler:nil)
            }
        case 3:
            profileTestScript("await pause(500);document.querySelector('[data-action=research-toggle]').click();await pause(200);return {name:document.querySelector('.profile-button').textContent,companies:document.querySelectorAll('.watchlist article').length,privateNoteVisible:document.body.textContent.includes('PRIVATE PROFILE UI TEST')};"){value in
                profileResults["bobIsolation"]=value
                do{profileResults["bobHasNoKey"]=try self.profiles.loadAPIKey()==nil}catch{profileResults["keychainError"]=error.localizedDescription}
                self.webView.evaluateJavaScript("document.querySelector('.profile-button').click();setTimeout(()=>document.querySelector('.profile-overlay .primary').click(),100)",completionHandler:nil)
            }
        case 4:
            profileTestScript("await pause(400);return document.querySelectorAll('.account-option').length;"){value in
                profileResults["accountCount"]=value;self.fillTestProfileDialog("QA Alice")
                self.webView.evaluateJavaScript("document.querySelector('.account-option').click()",completionHandler:nil)
            }
        case 5:
            profileTestScript("await pause(500);document.querySelector('[data-action=research-toggle]').click();await pause(200);document.querySelector('.thesis-editor').open=true;return document.querySelector('[data-note=thesis]').value;"){value in
                profileResults["aliceRestoredNote"]=value
                do{profileResults["keyRestored"]=try self.profiles.loadAPIKey()=="sk-test-not-a-real-key-501";try self.profiles.forgetAPIKey();profileResults["keyRemoved"]=try self.profiles.loadAPIKey()==nil}catch{profileResults["keychainRestoreError"]=error.localizedDescription}
                self.finishProfileTest()
            }
        default:self.finishProfileTest("Unexpected profile navigation")
        }
    }
}
