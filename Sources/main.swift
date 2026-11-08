// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import AppKit
import WebKit
import PDFKit
import UniformTypeIdentifiers

// Tickertwister Desktop: local interface and calculations, HTTPS-only data access.
final class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate, NSWindowDelegate {
    func aiArchiveURL() throws -> URL {
        let base=try researchURL()
        let dir=base.deletingPathExtension().appendingPathExtension("ai-archive")
        try FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        return dir
    }
    func saveAIRecord(_ record:[String:Any]) throws {
        guard let id=record["id"] as? String,UUID(uuidString:id) != nil,
              let input=record["input"] as? [String:Any],let companies=input["companies"] as? [[String:Any]],(1...4).contains(companies.count),
              let language=record["language"] as? String,Localization.languages.contains(language),
              let response=record["response"] as? [String:Any],response["status"] as? String=="completed",
              let data=try? JSONSerialization.data(withJSONObject:record),data.count<250000 else {throw NSError(domain:"AI_ARCHIVE",code:1)}
        let url=try aiArchiveURL().appendingPathComponent(id+".json")
        try writePrivate(data,to:url)
        try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:url.path)
    }

    var profileTesting:Bool {testing && CommandLine.arguments.contains("--profile-test")}
    var usesProfiles:Bool {!testing || profileTesting}
    var supportDirectory:URL {
        if profileTesting,let output=testOutput{return URL(fileURLWithPath:output+".profile-data",isDirectory:true)}
        return FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0].appendingPathComponent("Tickertwister",isDirectory:true)
    }
    lazy var profiles=ProfileStore(root:supportDirectory.appendingPathComponent("Profiles",isDirectory:true))
    var aiKey: String?
    var aiBusy=false
    let aiSession: URLSession = {
        let c=URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest=240;c.timeoutIntervalForResource=300
        return URLSession(configuration:c)
    }()
    @objc func showLicense(){if let url=Bundle.main.resourceURL?.appendingPathComponent("Source"){NSWorkspace.shared.open(url)}}
    func aiInterpret(_ body:[String:Any],_ id:Int){
        let outputLanguage=body["language"] as? String ?? "en"
        guard Localization.languages.contains(outputLanguage) else {reply(id,false,["error":"INVALID_LANGUAGE"]);return}
        let uiLanguage=body["uiLanguage"] as? String ?? Localization.current
        func text(_ key:String)->String{Localization.text(key,uiLanguage)}
        func fail(_ a:String,_ b:String){reply(id,false,["error":text(b)])}
        guard !aiBusy else{fail("AI-aanvraag loopt al.","An AI request is already running.");return}
        guard let request=body["request"] as? [String:Any],
              let model=request["model"] as? String,["gpt-6-luna","gpt-6.1-sol","gpt-6-astra"].contains(model),request["store"] as? Bool == false,
              let limit=request["max_output_tokens"] as? Int,[4096,8192,16384].contains(limit),request["tools"] == nil,
              let reasoning=request["reasoning"] as? [String:Any],let effort=reasoning["effort"] as? String,["low","medium","high"].contains(effort),
              let input=request["input"] as? String,input.utf8.count<=64000,
              let context=body["context"] as? [String:Any],
              let contextData=try? JSONSerialization.data(withJSONObject:context),contextData.count<=64000,
              let encoded=try? JSONSerialization.data(withJSONObject:request),encoded.count<96000 else{
            fail("Ongeldige AI-aanvraag.","Invalid AI request.");return
        }
        if aiKey == nil && profiles.active != nil {
            do {aiKey=try profiles.loadAPIKey()}catch{fail("Sleutelhanger niet toegankelijk. Ontgrendel deze via macOS of gebruik Vergeet API-sleutel om opnieuw te beginnen.","Keychain unavailable. Unlock it in macOS or use Forget API key to start again.");return}
        }
        if aiKey == nil {
            let alert=NSAlert();alert.messageText="OpenAI API · AI-AIC"
            alert.informativeText=text("Enter your own API key. This paid request sends the displayed financial data to OpenAI. Optionally select Save in Keychain. The key is additionally encrypted for this account. Without an account it stays in memory only.")
            let accessory=NSView(frame:NSRect(x:0,y:0,width:400,height:70))
            let field=NSSecureTextField(frame:NSRect(x:0,y:38,width:400,height:28));field.placeholderString="OpenAI API key";accessory.addSubview(field)
            let remember=NSButton(checkboxWithTitle:text("Save in macOS Keychain"),target:nil,action:nil);remember.frame=NSRect(x:0,y:0,width:400,height:28);remember.isEnabled=profiles.active != nil;accessory.addSubview(remember);alert.accessoryView=accessory
            alert.addButton(withTitle:text("Use key"));alert.addButton(withTitle:text("Cancel"))
            alert.window.initialFirstResponder=field
            guard alert.runModal()==NSApplication.ModalResponse.alertFirstButtonReturn else{fail("Geannuleerd; geen API-aanroep.","Cancelled; no API call.");return}
            let key=field.stringValue.trimmingCharacters(in:.whitespacesAndNewlines);field.stringValue=""
            guard key.hasPrefix("sk-"),key.count>=20,key.count<512,!key.contains("\n") else{fail("Ongeldige sleutelvorm.","Invalid key format.");return}
            if remember.state == .on {do{try profiles.saveAPIKey(key)}catch{fail("Bewaren in sleutelhanger mislukt; geen API-aanvraag verstuurd.","Could not save to Keychain; no API request sent.");return}}
            aiKey=key
        }
        aiBusy=true
        var req=URLRequest(url:URL(string:"https://api.openai.com/v1/responses")!)
        req.httpMethod="POST";req.httpBody=encoded
        req.setValue("application/json",forHTTPHeaderField:"Content-Type")
        req.setValue("Bearer \(aiKey!)",forHTTPHeaderField:"Authorization")
        aiSession.dataTask(with:req){[weak self] data,response,error in
            DispatchQueue.main.async {
                guard let self=self else{return};self.aiBusy=false
                func failed(_ a:String,_ b:String){self.reply(id,false,["error":text(b)])}
                guard error==nil else{failed("Netwerkfout of timeout. Geen automatische herhaling; de aanvraag kan al kosten hebben gemaakt.","Network error or timeout. No automatic retry; this request may already have incurred costs.");return}
                let status=(response as? HTTPURLResponse)?.statusCode ?? 0
                guard status==200 else{
                    if status==401{self.aiKey=nil;failed("API-sleutel geweigerd. Probeer een geldige sleutel.","API key rejected. Enter a valid key.")}
                    else if status==403 || status==404 {failed("Dit model is niet beschikbaar voor jouw API-project. Kies zelf een ander model; er wordt niet automatisch opnieuw geprobeerd.","This model is unavailable to your API project. Select another model yourself; no automatic retry.")}
                    else if status==429{failed("API-limiet of tegoed ontoereikend. Controleer je API-account.","API limit or insufficient credit. Check your API account.")}
                    else{failed("OpenAI-aanvraag mislukt (HTTP \(status)). Geen automatische herhaling.","OpenAI request failed (HTTP \(status)). No automatic retry.")};return
                }
                guard let data=data,data.count<200000,let result=try? JSONSerialization.jsonObject(with:data) as? [String:Any] else{failed("Ongeldig API-antwoord.","Invalid API response.");return}
                var returned=result
                if result["status"] as? String == "completed" {
                    let record:[String:Any]=["id":UUID().uuidString,"input":context,"language":outputLanguage,"response":result,"createdAt":ISO8601DateFormatter().string(from:Date()),"translationOf":body["translationOf"] as? String ?? NSNull(),"settings":["model":model,"effort":effort,"limit":limit]]
                    returned["_archiveRecord"]=record
                    do {try self.saveAIRecord(record)} catch {returned["_archiveError"]="ARCHIVE_SAVE_FAILED"}
                }
                self.reply(id,true,returned)
            }
        }.resume()
    }

    var window: NSWindow!
    var webView: WKWebView!
    var webRoot: URL!
    var pendingOpen: URL?
    var printView: WKWebView?
    var printPageCount=2
    var printRequestID: Int?
    var printData=NSMutableData()
    var printContext: CGContext?
    var printOutput: String?
    var researchDirty=false
    var ready = false
    var engineProcesses: [UUID: Process] = [:]
    var testing = false
    var testOutput: String?
    var testStart = Date()
    let session: URLSession = {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = 25
        configuration.timeoutIntervalForResource = 30
        configuration.httpMaximumConnectionsPerHost = 2
        return URLSession(configuration: configuration)
    }()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        let args = CommandLine.arguments
        if let i = args.firstIndex(of: "--smoke-test"), args.count > i + 1 { testing = true; testOutput = args[i + 1] }
        if testing {
            FileHandle.standardError.write(Data("Self-test: app launched\n".utf8))
            DispatchQueue.main.asyncAfter(deadline:.now()+175){
                if let output=self.testOutput {try? "{\"error\":\"Startup timeout\"}".write(toFile:output,atomically:true,encoding:.utf8)}
                NSApp.terminate(nil)
            }
        }
        webRoot = Bundle.main.resourceURL!.appendingPathComponent("Web", isDirectory: true)
        let controller = WKUserContentController()
        controller.add(self, name: "desktop")
        if let zoneData = try? JSONEncoder().encode(TimeZone.autoupdatingCurrent.identifier), let zone = String(data:zoneData,encoding:.utf8) { controller.addUserScript(WKUserScript(source:"window.__ttTimeZone=\(zone);",injectionTime:.atDocumentStart,forMainFrameOnly:true)) }
        if testing && !profileTesting {controller.addUserScript(WKUserScript(source:"window.__tickertwisterTestTicker='AAPL';",injectionTime:.atDocumentStart,forMainFrameOnly:true))}
        if testing,let i=args.firstIndex(of:"--studio-fixture"),args.count>i+1,let fixture=try? Data(contentsOf:URL(fileURLWithPath:args[i+1])) {
            controller.addUserScript(WKUserScript(source:"window.__studioFixture=JSON.parse(new TextDecoder().decode(Uint8Array.from(atob('\(fixture.base64EncodedString())'),c=>c.charCodeAt(0))));",injectionTime:.atDocumentStart,forMainFrameOnly:true))
        }
        if testing,let i=args.firstIndex(of:"--test-theme"),args.count>i+1,["professional","modern","futuristic","library"].contains(args[i+1]) {
            controller.addUserScript(WKUserScript(source:"window.__testTheme='\(args[i+1])';localStorage.setItem('tt-theme','\(args[i+1])');",injectionTime:.atDocumentStart,forMainFrameOnly:true))
        }
        if testing,args.contains("--dossier-test") {controller.addUserScript(WKUserScript(source:"window.__longNotes=true;",injectionTime:.atDocumentStart,forMainFrameOnly:true))}
        if testing,args.contains("--collection-test") {controller.addUserScript(WKUserScript(source:"window.__collectionTest=true;",injectionTime:.atDocumentStart,forMainFrameOnly:true))}
        if testing,let i=args.firstIndex(of:"--test-language"),args.count>i+1,Localization.languages.contains(args[i+1]) {
            controller.addUserScript(WKUserScript(source:"localStorage.setItem('tt-language','\(args[i+1])');",injectionTime:.atDocumentStart,forMainFrameOnly:true))
        }
        let config = WKWebViewConfiguration()
        config.userContentController = controller
        config.websiteDataStore = testing ? .nonPersistent() : .default()
        config.defaultWebpagePreferences.allowsContentJavaScript = true
        webView = WKWebView(frame: NSRect(x:0,y:0,width:1240,height:900),configuration: config)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = false
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:1240,height:900),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.delegate=self
        window.title = "Tickertwister Desktop"
        window.minSize = NSSize(width:820,height:620)
        window.contentView = webView
        window.setFrameAutosaveName("TickertwisterMainWindow")
        if testing{window.setContentSize(NSSize(width:args.contains("--compact-test") ? 900 : 1240,height:900))}
        window.center()
        buildMenu()
        let url = webRoot.appendingPathComponent("index.html")
        webView.loadFileURL(url,allowingReadAccessTo:webRoot)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps:true)
    }
    func applicationWillTerminate(_ notification:Notification){for process in engineProcesses.values where process.isRunning {process.terminate()}}
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool { true }
    func application(_ sender:NSApplication,openFiles filenames:[String]) {
        if CommandLine.arguments.contains("--smoke-test"){return}
        guard let path=filenames.first else { return }
        let url=URL(fileURLWithPath:path)
        if ready { openReport(url) } else { pendingOpen=url }
    }
    func buildMenu() {
        let bar=NSMenu()
        let appItem=NSMenuItem();let appMenu=NSMenu();appItem.submenu=appMenu;bar.addItem(appItem)
        appMenu.addItem(withTitle:Localization.text("About Tickertwister Desktop"),action:#selector(about),keyEquivalent:"").target=self
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle:Localization.text("Hide Tickertwister"),action:#selector(NSApplication.hide(_:)),keyEquivalent:"h")
        appMenu.addItem(withTitle:Localization.text("Quit Tickertwister"),action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q")
        let fileItem=NSMenuItem(title:Localization.text("File"),action:nil,keyEquivalent:"");let file=NSMenu(title:Localization.text("File"));fileItem.submenu=file;bar.addItem(fileItem)
        for (title,action,key) in [(Localization.text("New analysis"),#selector(newAnalysis),"n"),(Localization.text("Open analysis…"),#selector(openDialog),"o"),(Localization.text("Save analysis"),#selector(saveAnalysis),"s"),(Localization.text("Print / save as PDF…"),#selector(printReport),"p")] {
            file.addItem(withTitle:title,action:action,keyEquivalent:key).target=self
        }
        let editItem=NSMenuItem(title:Localization.text("Edit"),action:nil,keyEquivalent:"");let edit=NSMenu(title:Localization.text("Edit"));editItem.submenu=edit;bar.addItem(editItem)
        for (title,selector,key) in [(Localization.text("Undo"),"undo:","z"),(Localization.text("Cut"),"cut:","x"),(Localization.text("Copy"),"copy:","c"),(Localization.text("Paste"),"paste:","v"),(Localization.text("Select all"),"selectAll:","a")] { edit.addItem(withTitle:title,action:NSSelectorFromString(selector),keyEquivalent:key) }
        edit.addItem(withTitle:Localization.text("Find in this view…"),action:#selector(findInPage),keyEquivalent:"f").target=self
        let helpItem=NSMenuItem(title:Localization.text("Help"),action:nil,keyEquivalent:"");let help=NSMenu(title:Localization.text("Help"));helpItem.submenu=help;bar.addItem(helpItem)
        for (code,name) in [("nl","Nederlands"),("en","English"),("fr","Français"),("de","Deutsch"),("es","Español"),("it","Italiano"),("pt","Português")] {
            let item=help.addItem(withTitle:"📖 "+name,action:#selector(showLocalizedHelp(_:)),keyEquivalent:"")
            item.representedObject=code;item.target=self
        }
        help.addItem(withTitle:Localization.text("License and source"),action:#selector(showLicense),keyEquivalent:"").target=self
        NSApp.mainMenu=bar
    }
    @objc func about(){
        let style=NSMutableParagraphStyle();style.alignment = .center;style.paragraphSpacing=12
        let credits=NSAttributedString(string:"Research Studio\n"+Localization.text("Initial screening, not investment advice.")+"\nAGPLv3 · "+Localization.text("No warranty"),attributes:[.font:NSFont.systemFont(ofSize:13),.paragraphStyle:style,.foregroundColor:NSColor.secondaryLabelColor])
        NSApp.orderFrontStandardAboutPanel(options:[.applicationName:"Tickertwister Desktop",.applicationVersion:Bundle.main.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? "",.credits:credits])
    }
    @objc func showLocalizedHelp(_ item:NSMenuItem){
        let code=item.representedObject as? String ?? "en"
        let resource=code=="nl" ? "Handleiding":"User-Guide-"+code.uppercased()
        if let url=Bundle.main.url(forResource:resource,withExtension:"pdf"){NSWorkspace.shared.open(url)}
    }
    @objc func showEnglishHelp(){if let url=Bundle.main.url(forResource:"User-Guide-EN",withExtension:"pdf"){NSWorkspace.shared.open(url)}}
    @objc func showHelp(){if let url=Bundle.main.url(forResource:"Handleiding",withExtension:"pdf") ?? Bundle.main.url(forResource:"Handleiding",withExtension:"html"){NSWorkspace.shared.open(url)}}
    func dispatch(_ name:String,_ object:Any?=nil){
        var detail="null"
        if let object=object,let data=try? JSONSerialization.data(withJSONObject:object,options:[.fragmentsAllowed]),let text=String(data:data,encoding:.utf8){detail=text}
        webView.evaluateJavaScript("window.dispatchEvent(new CustomEvent('\(name)',{detail:\(detail)}));",completionHandler:nil)
    }
    @objc func findInPage(){dispatch("desktop-find")}
    @objc func newAnalysis(){dispatch("desktop-new")}
    @objc func saveAnalysis(){dispatch("desktop-save")}
    @objc func openDialog(){chooseOpen(id:nil)}
    @objc func printReport(){dispatch("desktop-print")}
    func preparePrint(_ html:String,id:Int?){
        guard printView == nil,html.utf8.count<2_000_000 else {if let id=id{reply(id,false,["error":"PRINT_FAILED"])};return}
        if testing{FileHandle.standardError.write(Data("Self-test: preparing report\n".utf8))}
        printRequestID=id
        printData=NSMutableData()
        var paper=CGRect(x:0,y:0,width:595.28,height:841.89)
        guard let consumer=CGDataConsumer(data:printData),let context=CGContext(consumer:consumer,mediaBox:&paper,nil) else{failPrint();return}
        printContext=context
        let config=WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        let view=WKWebView(frame:NSRect(x:0,y:0,width:794,height:1123),configuration:config)
        view.navigationDelegate=self
        printView=view
        view.loadHTMLString(html,baseURL:webRoot)
    }
    func exportPrintPage(_ index:Int){
        guard let view=printView,let context=printContext else{return}
        if index==printPageCount {
            context.closePDF()
            guard let document=PDFDocument(data:printData as Data) else{failPrint();return}
            if let output=printOutput {
                let success=self.printData.write(to:URL(fileURLWithPath:output+".pdf"),atomically:true)
                FileHandle.standardError.write(Data("Print self-test: \(success), pages: \(document.pageCount)\n".utf8))
                self.webView.callAsyncJavaScript("document.querySelector('.brand').click();await new Promise(r=>setTimeout(r,100));return {home:!!document.querySelector('.hero'),deskHidden:document.querySelector('#research-desk')?.getBoundingClientRect().height===0,scrollTop:window.scrollY};",arguments:[:],in:nil,in:.page){result in
                    if case .success(let object)=result,let data=try? JSONSerialization.data(withJSONObject:object){try? data.write(to:URL(fileURLWithPath:output+".reset.json"))}
                    NSApp.terminate(nil)
                }
            }else{
                let info=NSPrintInfo.shared.copy() as! NSPrintInfo
                info.paperSize=NSSize(width:595.28,height:841.89)
                info.topMargin=0;info.bottomMargin=0;info.leftMargin=0;info.rightMargin=0
                if let operation=document.printOperation(for:info,scalingMode:.pageScaleToFit,autoRotate:false){
                    operation.showsPrintPanel=true;operation.showsProgressPanel=true
                    operation.run()
                }
                if let id=printRequestID{reply(id,true,["done":true])}
            }
            printView=nil;printContext=nil;printRequestID=nil;return
        }
        view.evaluateJavaScript("document.querySelectorAll('.print-page').forEach((p,i)=>p.style.display=i===\(index)?'block':'none'); document.body.offsetHeight"){_,error in
        guard error==nil else{self.failPrint();return}
        let configuration=WKPDFConfiguration()
        configuration.rect=CGRect(x:0,y:0,width:794,height:1123)
        view.createPDF(configuration:configuration){result in
            switch result {
            case .success(let data):
                guard let page=PDFDocument(data:data)?.page(at:0),let reference=page.pageRef else {self.failPrint();return}
                context.beginPDFPage(nil)
                context.saveGState()
                context.scaleBy(x:595.28/794,y:841.89/1123)
                context.drawPDFPage(reference)
                context.restoreGState()
                context.endPDFPage()
                self.exportPrintPage(index+1)
            case .failure: self.failPrint()
            }
        }
        }
    }
    func failPrint(){
        if let id=printRequestID{reply(id,false,["error":"PRINT_FAILED"])}
        printView=nil;printContext=nil;printRequestID=nil
        if testing{NSApp.terminate(nil)}
    }
    func reply(_ id:Int,_ ok:Bool,_ object:Any){
        guard let data=try? JSONSerialization.data(withJSONObject:object,options:[.fragmentsAllowed]) else{return}
        webView.evaluateJavaScript("window.__tickertwisterReply(\(id),\(ok ? "true":"false"),'\(data.base64EncodedString())');",completionHandler:nil)
    }
    func confirmDiscardResearch()->Bool {
        if aiBusy && !testing {
            let alert=NSAlert();alert.messageText=Localization.text("AI request in progress")
            alert.informativeText=Localization.text("Quitting may lose a paid response. Wait until it is saved locally.")
            alert.addButton(withTitle:Localization.text("Keep waiting"));alert.addButton(withTitle:Localization.text("Quit anyway"))
            if alert.runModal() != .alertSecondButtonReturn{return false}
        }
        guard researchDirty,!testing else{return true}
        let alert=NSAlert()
        alert.messageText=Localization.text("Unsaved research changes")
        alert.informativeText=Localization.text("Your notes or watchlist have not been saved. Cancel and save your dossier changes first.")
        alert.addButton(withTitle:Localization.text("Cancel"))
        alert.addButton(withTitle:Localization.text("Discard changes"))
        let discard=alert.runModal() == .alertSecondButtonReturn
        if discard{researchDirty=false}
        return discard
    }
    func windowShouldClose(_ sender:NSWindow)->Bool {confirmDiscardResearch()}
    func applicationShouldTerminate(_ sender:NSApplication)->NSApplication.TerminateReply {confirmDiscardResearch() ? .terminateNow : .terminateCancel}
    func researchURL() throws -> URL {
        if testing && !profileTesting,let output=testOutput {return URL(fileURLWithPath:output+".research.json")}
        if profiles.active != nil {return try profiles.privateURL("research.json")}
        if !(try profiles.accounts()).isEmpty {throw profiles.failure("PROFILE_LOCKED")}
        let directory=supportDirectory
        try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        return directory.appendingPathComponent("research.json")
    }
    func loadCompanyIcon(_ website:String,id:Int){
        guard let url=URL(string:website),["http","https"].contains(url.scheme ?? ""),let host=url.host,
          host.range(of:"^[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*\\.[A-Za-z]{2,63}$",options:.regularExpression) != nil,
          !host.hasSuffix(".local"),!host.hasSuffix(".internal"),url.port==nil,url.user==nil,url.password==nil else{reply(id,false,["error":"NO_LOGO"]);return}
        let root="https://"+host
        var candidates=[root+"/apple-touch-icon.png",root+"/favicon.ico"]
        if host=="www.coca-colacompany.com" || host=="coca-colacompany.com" {
            candidates.insert("https://www.coca-colacompany.com/content/dam/corporate/us/en/tccc/home/carousel/tccc-icon.jpg",at:0)
        }
        func attempt(_ index:Int){
            guard index<candidates.count,let target=URL(string:candidates[index]) else{self.reply(id,false,["error":"NO_LOGO"]);return}
            var request=URLRequest(url:target);request.timeoutInterval=5
            self.session.dataTask(with:request){data,response,error in DispatchQueue.main.async {
                guard error==nil,let http=response as? HTTPURLResponse,http.statusCode==200,http.url?.scheme=="https",
                  let finalHost=http.url?.host,(finalHost==host || finalHost=="www."+host || "www."+finalHost==host),
                  let data=data,data.count<2_000_000,let bitmap=NSBitmapImageRep(data:data),bitmap.pixelsWide<=2048,bitmap.pixelsHigh<=2048,
                  let png=bitmap.representation(using:.png,properties:[:]) else{attempt(index+1);return}
                self.reply(id,true,["image":"data:image/png;base64,"+png.base64EncodedString(),"source":http.url!.absoluteString])
            }}.resume()
        }
        attempt(0)
    }

    func allowed(_ url:URL)->Bool {
        guard url.scheme=="https",url.user==nil,url.password==nil,url.port==nil else { return false }
        switch url.host {
        case "www.sec.gov": return url.path=="/files/company_tickers.json" && url.query==nil
        case "data.sec.gov": return url.path.range(of:"^/api/xbrl/companyfacts/CIK[0-9]{10}\\.json$",options:.regularExpression) != nil && url.query==nil
        case "query1.finance.yahoo.com": return url.path.range(of:"^/v8/finance/chart/[A-Z0-9][A-Z0-9.\\-]{0,19}$",options:.regularExpression) != nil && url.query=="interval=1d&range=5d"
        default:return false
        }
    }
    func userContentController(_ controller:WKUserContentController,didReceive message:WKScriptMessage){
        guard message.frameInfo.isMainFrame,message.webView===webView,
              message.frameInfo.request.url?.isFileURL==true,
              let body=message.body as? [String:Any],let id=body["id"] as? Int,let action=body["action"] as? String else{return}
        if action.hasPrefix("profile-"){profileAction(action,body,id);return}
        if usesProfiles {
            do {if !(try profiles.accounts()).isEmpty && profiles.active==nil {reply(id,false,["error":"PROFILE_LOCKED"]);return}}
            catch{reply(id,false,["error":"ACCOUNT_INDEX_INVALID"]);return}
        }
        switch action {
        case "set-language":
            if let language=body["language"] as? String,Localization.languages.contains(language){Localization.current=language;UserDefaults.standard.set(language,forKey:"appLanguage");buildMenu()}
            reply(id,true,["done":true])
        case "ai-interpret": aiInterpret(body,id)
        case "ai-archive-list":
            do {
                let urls=try FileManager.default.contentsOfDirectory(at:aiArchiveURL(),includingPropertiesForKeys:[.fileSizeKey]).filter{$0.pathExtension=="json"}
                var records=[[String:Any]]();var invalid=0
                for url in urls {
                    guard let size=try? url.resourceValues(forKeys:[.fileSizeKey]).fileSize,size<250000,
                          let data=try? readPrivate(url),let record=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] else{invalid+=1;continue}
                    records.append(record)
                }
                reply(id,true,["records":records,"invalid":invalid])
            }catch{reply(id,false,["error":"ARCHIVE_READ_FAILED"])}
        case "ai-archive-save":
            do {guard let record=body["record"] as? [String:Any] else{throw NSError(domain:"AI_ARCHIVE",code:1)};try saveAIRecord(record);reply(id,true,["saved":true])}catch{reply(id,false,["error":"ARCHIVE_SAVE_FAILED"])}
        case "ai-clear":
            aiKey=nil
            do{if profiles.active != nil {try profiles.forgetAPIKey()};reply(id,true,["done":true])}catch{reply(id,false,["error":"KEYCHAIN_DELETE_FAILED"])}
        case "company-logo":
            guard let website=body["website"] as? String else{reply(id,false,["error":"NO_LOGO"]);return}
            loadCompanyIcon(website,id:id)
        case "research-dirty": researchDirty=body["dirty"] as? Bool ?? false;reply(id,true,["done":true])
        case "research-load":
            do {
                let url=try researchURL()
                if FileManager.default.fileExists(atPath:url.path){
                    let attrs=try FileManager.default.attributesOfItem(atPath:url.path)
                    guard ((attrs[.size] as? NSNumber)?.intValue ?? Int.max)<5_000_000 else{reply(id,false,["error":"INVALID_DESK"]);return}
                    guard let content=String(data:try readPrivate(url),encoding:.utf8) else{throw profiles.failure("INVALID_DESK")}
                    reply(id,true,["content":content])
                }else{reply(id,true,["content":NSNull()])}
            }catch{reply(id,false,["error":"DESK_READ_FAILED"])}
        case "research-save":
            guard let content=body["content"] as? String,let data=content.data(using:.utf8),data.count<5_000_000,
                  let object=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],object["format"] as? String=="tickertwister-research",object["version"] as? Int==1,
                  let entries=object["entries"] as? [[String:Any]],entries.count<=30 else{reply(id,false,["error":"INVALID_DESK"]);return}
            do {
                let url=try researchURL(),backup=url.appendingPathExtension("backup")
                if FileManager.default.fileExists(atPath:url.path){try Data(contentsOf:url).write(to:backup,options:.atomic);try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:backup.path)}
                try writePrivate(data,to:url)
                try FileManager.default.setAttributes([.posixPermissions:0o600],ofItemAtPath:url.path)
                reply(id,true,["saved":true])
            }catch{reply(id,false,["error":"DESK_SAVE_FAILED"])}
        case "analyse":
            if testing,let i=CommandLine.arguments.firstIndex(of:"--analysis-fixture"),CommandLine.arguments.count>i+1,
               let data=try? Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[i+1])),let fixture=try? JSONSerialization.jsonObject(with:data){reply(id,true,fixture);return}
            guard let symbol=body["symbol"] as? String,symbol.range(of:"^[A-Z0-9^][A-Z0-9.^=\\-]{0,19}$",options:.regularExpression) != nil else {reply(id,false,["error":"INVALID_TICKER"]);return}
            guard engineProcesses.count<2 else {reply(id,false,["error":"ENGINE_BUSY"]);return}
            let process=Process(), pipe=Pipe(), token=UUID()
            process.executableURL=Bundle.main.resourceURL!.appendingPathComponent("Engine/YahooEngine")
            process.arguments=[symbol]
            var environment=ProcessInfo.processInfo.environment
            environment.removeValue(forKey:"PYTHONHOME");environment.removeValue(forKey:"PYTHONPATH")
            let cache=FileManager.default.urls(for:.cachesDirectory,in:.userDomainMask)[0].appendingPathComponent("Tickertwister/yfinance")
            try? FileManager.default.createDirectory(at:cache,withIntermediateDirectories:true)
            environment["TICKERTWISTER_CACHE"]=cache.path
            process.environment=environment
            process.standardOutput=pipe;process.standardError=FileHandle.nullDevice
            do {try process.run()}catch{reply(id,false,["error":"ENGINE_UNAVAILABLE"]);return}
            engineProcesses[token]=process
            DispatchQueue.main.asyncAfter(deadline:.now()+150){if self.engineProcesses[token]?.isRunning == true {self.engineProcesses[token]?.terminate()}}
            DispatchQueue.global(qos:.userInitiated).async {
                let data=pipe.fileHandleForReading.readDataToEndOfFile();process.waitUntilExit()
                DispatchQueue.main.async {
                    self.engineProcesses.removeValue(forKey:token)
                    guard data.count<5_000_000,let object=try? JSONSerialization.jsonObject(with:data) else {self.reply(id,false,["error":"YAHOO_UNAVAILABLE"]);return}
                    self.reply(id,true,object)
                }
            }
        case "fetch":
            guard let text=body["url"] as? String,let url=URL(string:text),allowed(url) else{reply(id,false,["error":"URL_NOT_ALLOWED"]);return}
            var request=URLRequest(url:url)
            request.setValue("TickertwisterDesktop/1.0 (+https://tickertwister-investor-bob.arcane-berry-6457.chatgpt.site)",forHTTPHeaderField:"User-Agent")
            request.setValue("application/json",forHTTPHeaderField:"Accept")
            session.dataTask(with:request){[weak self] data,response,error in
                DispatchQueue.main.async {
                    guard let self=self else{return}
                    guard error==nil,let response=response as? HTTPURLResponse,response.statusCode==200,let finalURL=response.url,self.allowed(finalURL),let data=data,data.count<25_000_000,let object=try? JSONSerialization.jsonObject(with:data) else{self.reply(id,false,["error":"DATA_UNAVAILABLE"]);return}
                    self.reply(id,true,object)
                }
            }.resume()
        case "print":
            guard let html=body["html"] as? String else {reply(id,false,["error":"PRINT_FAILED"]);return}
            preparePrint(html,id:id)
        case "open": chooseOpen(id:id)
        case "save":
            guard let content=body["content"] as? String,content.utf8.count<5_000_000,let name=body["filename"] as? String else{reply(id,false,["error":"INVALID_FILE"]);return}
            let panel=NSSavePanel();panel.title="Bewaar Tickertwister-analyse"
            panel.nameFieldStringValue=String(name.filter{!"/\\:".contains($0)}.prefix(100))
            panel.canCreateDirectories=true
            panel.beginSheetModal(for:window){[weak self] result in
                guard let self=self else{return}
                guard result == .OK,let url=panel.url else{self.reply(id,true,["cancelled":true]);return}
                do {try content.write(to:url,atomically:true,encoding:.utf8);self.reply(id,true,["saved":true])}catch{self.reply(id,false,["error":"SAVE_FAILED"])}
            }
        default:reply(id,false,["error":"UNKNOWN_ACTION"])
        }
    }
    func chooseOpen(id:Int?){
        let panel=NSOpenPanel();panel.title="Open Tickertwister-analyse";panel.canChooseDirectories=false;panel.allowsMultipleSelection=false
        panel.allowedContentTypes=[UTType(filenameExtension:"tickertwister") ?? .json,.json]
        panel.beginSheetModal(for:window){[weak self] response in
            guard let self=self else{return}
            if response == .OK,let url=panel.url { self.openReport(url) }
            if let id=id { self.reply(id,true,["done":true]) }
        }
    }
    func openReport(_ url:URL){
        if !testing && profiles.active==nil {guard (try? profiles.accounts().isEmpty)==true else {pendingOpen=url;return}}
        do {
            let attrs=try FileManager.default.attributesOfItem(atPath:url.path)
            guard ((attrs[.size] as? NSNumber)?.intValue ?? Int.max) < 5_000_000 else{throw NSError(domain:"file",code:1)}
            let data=try Data(contentsOf:url)
            let object=try JSONSerialization.jsonObject(with:data)
            dispatch("desktop-open-report",object)
        }catch {let alert=NSAlert();alert.messageText=Localization.text("This file cannot be opened.");alert.informativeText=Localization.text("Choose a saved .tickertwister analysis (maximum 5 MB).");alert.beginSheetModal(for:window)}
    }
    func webView(_ webView:WKWebView,decidePolicyFor action:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void){
        guard let url=action.request.url else{decisionHandler(.cancel);return}
        if webView === printView && (url.absoluteString=="about:blank" || url.standardizedFileURL.path==webRoot.standardizedFileURL.path){decisionHandler(.allow);return}
        if url.isFileURL && url.standardizedFileURL.path.hasPrefix(webRoot.standardizedFileURL.path+"/"){decisionHandler(.allow);return}
        if url.scheme=="https" && action.navigationType == .linkActivated {NSWorkspace.shared.open(url)}
        decisionHandler(.cancel)
    }
    func webView(_ webView:WKWebView,createWebViewWith configuration:WKWebViewConfiguration,for action:WKNavigationAction,windowFeatures:WKWindowFeatures)->WKWebView? {
        if let url=action.request.url,url.scheme=="https" {NSWorkspace.shared.open(url)}
        return nil
    }
    func webView(_ webView:WKWebView,didFinish navigation:WKNavigation!){
        if webView === printView {
            webView.evaluateJavaScript("JSON.stringify(Array.from(document.querySelectorAll('.print-page')).map(p=>({height:p.scrollHeight,footer:p.querySelector('.print-foot').offsetTop,last:p.querySelector('.print-foot').previousElementSibling.getBoundingClientRect().bottom-p.getBoundingClientRect().top})))"){result,_ in
                if self.testing,let output=self.printOutput,let text=result as? String{try? text.write(toFile:output+".layout.json",atomically:true,encoding:.utf8)}
                self.printView?.evaluateJavaScript("document.querySelectorAll('.print-page').length"){value,error in
                    guard error==nil,let count=value as? Int,count>0,count<=500 else{self.failPrint();return}
                    self.printPageCount=count;self.exportPrintPage(0)
                }
            };return
        }
        if testing {FileHandle.standardError.write(Data("Self-test: page loaded\n".utf8))}
        ready=true
        if let url=pendingOpen{pendingOpen=nil;DispatchQueue.main.asyncAfter(deadline:.now()+0.5){self.openReport(url)}}
        if profileTesting{testProfiles()}else if testing{testStart=Date();checkSmoke()}
    }
    // Internal integration harness: launches this app, observes rendered output, then exits.
    func webView(_ webView:WKWebView,didFailProvisionalNavigation navigation:WKNavigation!,withError error:Error){
        if testing {FileHandle.standardError.write(Data(("Load failure: "+error.localizedDescription+"\n").utf8))}
    }
    func saveSmokePDF(_ output:String){
        printOutput=output
        if CommandLine.arguments.contains("--dossier-test"){webView.evaluateJavaScript("document.querySelector('[data-action=\"desk-print\"]').click()") }else{dispatch("desktop-print")}
    }
    func testStudio(_ output:String){
        let script="""
        const pause=ms=>new Promise(r=>setTimeout(r,ms));
        const expand=[...document.querySelectorAll('header button')].find(b=>/Alles openvouwen|Expand all/.test(b.textContent));expand.click();await pause(100);expand.click();await pause(100);
        const editor=document.querySelector('.weight-editor');editor.closest('.work-fold').open=true;
        const collapsedWeightHeight=editor.getBoundingClientRect().height;
        editor.querySelector('summary').click();await pause(100);const weightOpensOnce=editor.open;
        editor.querySelector('summary').click();await pause(100);const weightClosesOnce=!editor.open&&editor.getBoundingClientRect().height<150;
        editor.closest('.work-fold').open=false;
        document.querySelector('[data-action="research-toggle"]').click();await pause(250);
        const loadedEntries=document.querySelectorAll('.watchlist article').length;
        const weight=document.querySelectorAll('.weight-editor input[type=number]')[4];Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(weight,'2');weight.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);
        document.querySelector('[data-action="desk-pin"]').click();await pause(250);
        document.querySelector('.thesis-editor').open=true;
        const area=document.querySelector('[data-note="thesis"]');
        Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(area,window.__longNotes?Array.from({length:150},(_,i)=>'Research note '+i+': cash generation and pricing power.').join(' '):'Test thesis: cash generation and pricing power.');
        area.dispatchEvent(new Event('input',{bubbles:true}));await pause(250);
        const status=document.querySelector('.thesis-editor .inputs select');status.value='candidate';status.dispatchEvent(new Event('change',{bubbles:true}));await pause(150);
        document.querySelector('[data-action="thesis-save"]').click();await pause(500);
        window.dispatchEvent(new CustomEvent('desktop-open-report',{detail:window.__studioFixture}));await pause(250);document.querySelector('[data-action="research-toggle"]').click();await pause(150);const w2=document.querySelectorAll('.weight-editor input[type=number]')[4];Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(w2,'2');w2.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);
        document.querySelector('[data-action="desk-pin"]').click();await pause(250);
        document.querySelector('[data-action="desk-save"]').click();await pause(500);
        document.querySelector('.watch-remove').click();await pause(80);document.querySelector('.watch-confirm button').click();await pause(80);const cancelKeptCompany=document.querySelectorAll('.watchlist article').length===2;
        document.querySelector('.watch-remove').click();await pause(80);document.querySelectorAll('.watch-confirm button')[1].click();await pause(100);
        document.querySelector('.desk-savebar button:not(.primary)').click();await pause(100);
        const undoRestoredCompany=document.querySelectorAll('.watchlist article').length===2;
        document.querySelectorAll('.watchlist input[type="checkbox"]').forEach(el=>{if(el.checked)el.click();});await pause(150);
        const activeAnalysisAvailable=!!document.querySelector('[data-action="interpret"]')&&!!document.querySelector('[data-action="ai-toggle"]');

        document.querySelectorAll('.watchlist input[type="checkbox"]').forEach(el=>{if(!el.checked)el.click();});await pause(100);
        document.querySelector('[data-action="desk-save"]').click();await pause(300);
        document.querySelector('[data-action="interpret"]').click();await pause(100);
        const interpreted=!!document.querySelector('.interpretation-studio .interpretation-text');
        document.querySelector('[data-action="interpret"]').click();await pause(100);const toggleClosed=!document.querySelector('.interpretation-text');document.querySelector('[data-action="interpret"]').click();await pause(100);
        document.querySelector('[data-action="list-view"]').click();await pause(100);const listView=!!document.querySelector('.watchlist-list');
        const chooser=document.querySelector('.period-select select');chooser.value=chooser.options[chooser.options.length-1].value;chooser.dispatchEvent(new Event('change',{bubbles:true}));await pause(100);
        const clearsStale=!document.querySelector('.interpretation-studio .interpretation-text');
        document.querySelector('[data-action="interpret"]').click();await pause(100);
        document.querySelector('#comparison').scrollIntoView();await pause(700);
        
        document.querySelector('.interpretation-choices>button:last-child').click();await pause(100);
        const aiConsentRequired=document.querySelector('.ai-aic .primary').disabled;const outputLanguage=document.querySelector('.ai-controls>label select:last-child');const languageSelect=[...document.querySelectorAll('.ai-controls select')].find(s=>[...s.options].some(o=>o.value==='nl'));const languageRequired=languageSelect.value==='auto';languageSelect.value='nl';languageSelect.dispatchEvent(new Event('change',{bubbles:true}));await pause(100);
        const modelSelect=document.querySelector('.ai-controls select');
        const defaultModel=modelSelect.value;
        document.querySelector('.ai-consent input').click();await pause(50);
        modelSelect.value='gpt-6-astra';modelSelect.dispatchEvent(new Event('change',{bubbles:true}));await pause(100);
        const modelChangeResetsConsent=!document.querySelector('.ai-consent input').checked&&document.querySelector('.ai-aic .primary').disabled;
        const selectedModel=document.querySelector('.ai-controls h4').textContent;
        const validModels=[...modelSelect.options].map(o=>o.value);
        const activeCard=document.querySelector('.watchlist article.active'),otherCard=document.querySelector('.watchlist article:not(.active)');const selectionTint=!!activeCard&&!!otherCard&&(getComputedStyle(activeCard).backgroundImage!==getComputedStyle(otherCard).backgroundImage||getComputedStyle(activeCard).backgroundColor!==getComputedStyle(otherCard).backgroundColor);
        const aiInput=JSON.parse(document.querySelector('.ai-input').textContent);
        const sections=Object.fromEntries(['comparability','profitability','balance_sheet','cash_flow','conclusion','follow_up','limitations'].map(k=>[k,'TEST ONLY: '+('Financial interpretation for archival and pagination testing. '.repeat(15))]));
        const rec={id:crypto.randomUUID(),input:aiInput,language:'nl',createdAt:new Date().toISOString(),response:{status:'completed',model:'local-test-fixture',usage:{input_tokens:0,output_tokens:0},output:[{content:[{type:'output_text',text:JSON.stringify(sections)}]}]}};
        window.webkit.messageHandlers.desktop.postMessage({id:-402,action:'ai-archive-save',record:rec});await pause(300);
        window.dispatchEvent(new Event('ai-archive-refresh'));await pause(300);
        const printBeforeSelection=document.querySelectorAll('#company-print .print-page').length;
        document.querySelectorAll('.ai-print-choice input').forEach(el=>{if(!el.checked)el.click();});await pause(150);
        const printAfterSelection=document.querySelectorAll('#company-print .print-page').length;
        const checkboxes=[...document.querySelectorAll('.watchlist input[type="checkbox"]')];if(checkboxes[1]?.checked)checkboxes[1].click();await pause(150);
        const singleCompanyAI=!!document.querySelector('.ai-aic')&&!!document.querySelector('[data-action="interpret"]');
        if(checkboxes[1]&&!checkboxes[1].checked)checkboxes[1].click();await pause(150);
        const aiPersisted=!!document.querySelector('.ai-result');
        const lang=document.querySelector('.language select');const oldLang=lang.value;lang.value=oldLang==='nl'?'en':'nl';lang.dispatchEvent(new Event('change',{bubbles:true}));await pause(200);
        const aiSurvivesLanguage=!!document.querySelector('.ai-result');
        lang.value=oldLang;lang.dispatchEvent(new Event('change',{bubbles:true}));await pause(200);
        const aiPrintPages=document.querySelectorAll('#company-print .print-page').length;
        const bookChildren=document.querySelector('#comparison').querySelectorAll(':scope>details').length;
        const aiNoNotes=!document.querySelector('.ai-input').textContent.includes('Test thesis');
        const thesisTitle=document.querySelector('.thesis-editor>summary').textContent;
        const companyTitle=document.querySelector('.thesis-editor h3').textContent;
        const prominentScore=document.querySelector('.score-kpi>strong').textContent;
        const originalScore=document.querySelector('.score-kpi .personal-score').textContent;
        document.querySelector('[data-action="research-toggle"]').click();await pause(100);const statementFold=document.querySelector('.statements').closest('.work-fold');statementFold.open=true;await pause(80);const statementTables=[...document.querySelectorAll('.statement-table')];const colEdges=statementTables.map(tb=>[...tb.querySelector('tbody tr').children].map(td=>td.getBoundingClientRect().right));const alignedColumns=colEdges[0].every((x,i)=>Math.abs(x-colEdges[1][i])<1);statementFold.open=false;document.querySelector('[data-action="research-toggle"]').click();await pause(100);
        const autoButton=document.querySelector('[data-action="interpret"]');if(autoButton.getAttribute('aria-expanded')!=='true')autoButton.click();await pause(100);
        const controls=document.querySelector('.ai-controls').getBoundingClientRect(),automatic=document.querySelector('.automatic-column').getBoundingClientRect(),fullResult=document.querySelector('.ai-result').getBoundingClientRect();const twoColumns=controls.left>automatic.left&&Math.abs(controls.width-automatic.width)<30;const fullWidthResult=fullResult.width>controls.width*1.8;
        document.querySelector('.interpretation-studio').scrollIntoView();await pause(700);
        const collectionFirst=!!(document.querySelector('.company-collection').compareDocumentPosition(document.querySelector('.thesis-editor'))&Node.DOCUMENT_POSITION_FOLLOWING);const settingsVisible=!!document.querySelector('.ai-settings')&&!document.querySelector('.ai-advanced');const disclaimerClosed=!document.querySelector('.ai-disclaimer').open;const separateView=document.querySelector('.analysis-view').hidden&&!document.querySelector('header .section-nav');const independentLanguage=languageSelect.value==='nl';const iconLoaded=document.querySelector('.app-mark').tagName.toLowerCase()==='svg';
        if(window.__collectionTest){document.querySelector('.thesis-editor').open=true;document.querySelector('.thesis-editor').scrollIntoView();await pause(600);}
        return {activeAnalysisAvailable,collectionFirst,settingsVisible,disclaimerClosed,separateView,languageRequired,independentLanguage,iconLoaded,defaultModel,modelChangeResetsConsent,selectedModel,validModels,selectionTint,alignedColumns,twoColumns,fullWidthResult,toggleClosed,listView,analysisOutsideComparison:!document.querySelector('#comparison .interpretation-studio'),historicalRows:document.querySelector('.history-series tbody')?.rows.length,shareCountRows:[...document.querySelectorAll('.value-panel dt')].filter(el=>/uitstaande|outstanding/.test(el.textContent)).length,collapsedWeightHeight,weightOpensOnce,weightClosesOnce,criterionSeries:document.querySelectorAll('.criterion-series').length,printBeforeSelection,printAfterSelection,singleCompanyAI,aiPersisted,aiSurvivesLanguage,aiPrintPages,bookChildren,aiConsentRequired,aiNoNotes,thesisTitle,companyTitle,prominentScore,originalScore,cancelKeptCompany,undoRestoredCompany,personalScoreVisible:!!document.querySelector('.personal-score'),nearSave:!!document.querySelector('[data-action="thesis-save"]'),comparisonFold:document.querySelector('#comparison').tagName,historyGrowth:!!document.querySelector('.historical-growth'),weightInputs:document.querySelectorAll('.weight-editor input[type=number]').length,labOrder:[...document.querySelectorAll('.work-fold>summary')].map(el=>el.textContent),theme:document.documentElement.dataset.theme,candidateBadge:!!document.querySelector('.status-candidate'),folds:document.querySelectorAll('.work-fold').length,closedFolds:document.querySelectorAll('.work-fold:not([open])').length,toolbarFixed:document.querySelector('header .report-toolbar')!==null,matrixMoved:document.querySelector('#valuation .heatmap')!==null,dossierPages:document.querySelectorAll('#research-print .print-page').length,interpreted,clearsStale,headerTop:document.querySelector('header').getBoundingClientRect().top,headerPosition:getComputedStyle(document.querySelector('header')).position,period:chooser.value,ratioDates:[...document.querySelectorAll('.ratios thead th')].map(n=>n.textContent),loadedEntries,entries:document.querySelectorAll('.watchlist article').length,comparisonColumns:document.querySelector('.comparison table')?.querySelectorAll('thead th').length,scenarios:document.querySelectorAll('.scenario').length,qualityChecks:document.querySelectorAll('.quality-item').length,heatmapCells:document.querySelectorAll('.heatmap td button').length,saved:document.querySelector('.desk-actions [role="status"]').textContent};
        """
        webView.callAsyncJavaScript(script,arguments:[:],in:nil,in:.page){result in
            if case .success(let object)=result,let data=try? JSONSerialization.data(withJSONObject:object){try? data.write(to:URL(fileURLWithPath:output+".studio.json"))}
            if case .failure(let error)=result{FileHandle.standardError.write(Data("Studio test failed: \(error)\n".utf8))}
            let config=WKSnapshotConfiguration();config.rect=self.webView.bounds
            self.webView.takeSnapshot(with:config){image,_ in
                if let image=image,let tiff=image.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]){try? png.write(to:URL(fileURLWithPath:output+".desk.png"))}
                self.webView.evaluateJavaScript("document.querySelector('[data-action=research-toggle]').click()")
                self.webView.evaluateJavaScript(CommandLine.arguments.contains("--criteria-test") ? "const card=document.querySelector('.score-details');card.closest('.work-fold').open=true;[...card.querySelectorAll('.compact-disclosures>details')].slice(4,10).forEach(d=>d.open=true);card.querySelectorAll('.compact-disclosures>details')[4].scrollIntoView()" : "document.getElementById('lab').closest('details').open=true;document.getElementById('lab').scrollIntoView()") {_,_ in
                    DispatchQueue.main.asyncAfter(deadline:.now()+0.5){
                        self.webView.takeSnapshot(with:config){image,_ in
                            if let image=image,let tiff=image.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]){try? png.write(to:URL(fileURLWithPath:output+".lab.png"))}
                            if CommandLine.arguments.contains("--refinement-test"){self.testRefinements(output,0)}else{self.saveSmokePDF(output)}
                        }
                    }
                }
            }
        }
    }
    func testRefinements(_ output:String,_ stage:Int){
        let stages:[(String,String)]=[
          ("value", "if(document.querySelector('.analysis-view').hidden)document.querySelector('[data-action=research-toggle]').click();await pause(100);document.querySelector('#valuation').scrollIntoView();return {fallback:document.querySelector('#valuation').textContent.includes('FCF'),value:document.querySelector('.value-panel>strong').textContent,step:[...document.querySelectorAll('#valuation input')].map(x=>x.step)};"),
          ("criteria", "const el=document.querySelector('.score-details');el.closest('.work-fold').open=true;el.querySelectorAll('.compact-disclosures>details').forEach(d=>d.open=false);el.scrollIntoView();const ds=[...el.querySelectorAll('.compact-disclosures>details')];return {count:ds.length,columns:getComputedStyle(el.querySelector('.compact-disclosures')).gridTemplateColumns};"),
          ("history", "const el=document.querySelector('.history-series');el.closest('.work-fold').open=true;el.scrollIntoView();return {columns:getComputedStyle(el.querySelector('.compact-disclosures')).gridTemplateColumns};"),
          ("search", "document.dispatchEvent(new KeyboardEvent('keydown',{key:'f',metaKey:true,bubbles:true}));await pause(100);const input=document.querySelector('.find-panel input');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'voorraaddagen');input.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));await pause(150);return {found:!!document.querySelector('.find-target'),findOpen:!!input,visible:document.querySelector('.find-target')?.getBoundingClientRect().height>0};"),
          ("thesis", "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));document.querySelector('[data-action=research-toggle]').click();await pause(150);const el=document.querySelector('.thesis-editor');el.open=true;el.scrollIntoView();const fields=[...el.querySelectorAll('textarea')].map(a=>a.getBoundingClientRect());const date=el.querySelector('input[type=date]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(date,'2026-12-01');date.dispatchEvent(new Event('input',{bubbles:true}));await pause(100);const time=el.querySelector('input[type=time]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(time,'14:35');time.dispatchEvent(new Event('input',{bubbles:true}));await pause(100);document.querySelector('[data-action=thesis-save]').click();await pause(250);return {twoColumns:fields[0].left===fields[1].left&&fields[2].left>fields[0].left,large:fields.every(x=>x.height>=170),date:date.value,time:time.value,removedDuplicate:!el.querySelector('.remove-company')};")
        ]
        if stage>=stages.count{webView.evaluateJavaScript("document.querySelector('[data-action=research-toggle]').click()"){_,_ in self.saveSmokePDF(output)};return}
        let item=stages[stage]
        webView.callAsyncJavaScript("const pause=ms=>new Promise(r=>setTimeout(r,ms));"+item.1,arguments:[:],in:nil,in:.page){result in
            if case .success(let object)=result,let data=try? JSONSerialization.data(withJSONObject:object){try? data.write(to:URL(fileURLWithPath:output+"."+item.0+".json"))}
            if case .failure(let error)=result{FileHandle.standardError.write(Data("Refinement test failed: \(error)\n".utf8))}
            DispatchQueue.main.asyncAfter(deadline:.now()+0.7){self.webView.takeSnapshot(with:nil){image,_ in
                if let tiff=image?.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]){try? png.write(to:URL(fileURLWithPath:output+"."+item.0+".png"))}
                self.testRefinements(output,stage+1)
            }}
        }
    }
    func testControls(_ output:String){
        let script = """
        const pause=ms=>new Promise(r=>setTimeout(r,ms));
        const result={steps:[]};
        for(const section of ['#valuation','#scenario']){
          const el=document.querySelector(section);if(el.closest('.work-fold'))el.closest('.work-fold').open=true;
          for(const input of el.querySelectorAll('input[type=number]')){
            const before=input.value,base=input.max&&Number(input.max)<15.2?5:15;input.value=String(base);input.stepUp();const first=input.value;input.stepUp();const second=input.value;input.value=before;
            result.steps.push({section,label:input.closest('label').textContent,first,second,pass:Number(first)===base+.1&&Number(second)===base+.2});
          }
        }
        result.stepsPass=result.steps.every(x=>x.pass);
        const growth=document.querySelectorAll('#valuation input')[1];const original=growth.value;
        const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
        set.call(growth,'27.1');growth.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);
        result.growthAccepted=!document.querySelector('#valuation .error')&&growth.value==='27.1';
        set.call(growth,original);growth.dispatchEvent(new Event('input',{bubbles:true}));await pause(150);
        const nav=document.querySelector('header>nav'),toolbar=document.querySelector('.context-toolbar');
        const bounds=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}};
        result.header=bounds(document.querySelector('header'));result.nav=bounds(nav);result.toolbar=bounds(toolbar);
        result.viewport=innerWidth;result.noHorizontalOverflow=document.documentElement.scrollWidth<=innerWidth;
        result.sameRibbon=Math.abs(document.querySelector('.section-nav').getBoundingClientRect().y-document.querySelector('.report-toolbar').getBoundingClientRect().y)<8;
        result.iconLabels=[...document.querySelectorAll('header .icon-action')].every(x=>x.title&&x.getAttribute('aria-label'));
        window.scrollTo(0,0);return result;
        """
        webView.callAsyncJavaScript(script,arguments:[:],in:nil,in:.page){result in
            if case .success(let object)=result,let data=try? JSONSerialization.data(withJSONObject:object){try? data.write(to:URL(fileURLWithPath:output+".controls.json"))}
            if case .failure(let error)=result{FileHandle.standardError.write(Data("Controls test failed: \(error)\n".utf8))}
            DispatchQueue.main.asyncAfter(deadline:.now()+0.3){self.webView.takeSnapshot(with:nil){image,_ in
                if let tiff=image?.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]){try? png.write(to:URL(fileURLWithPath:output+".controls.png"))}
                self.saveSmokePDF(output)
            }}
        }
    }
    func checkSmoke(){
        webView.evaluateJavaScript("JSON.stringify({title:document.title,charts:document.querySelectorAll('.work-fold .chart-grid .chart svg').length,criteria:document.querySelectorAll('.score-details .compact-disclosures>details').length,profile:!!document.querySelector('.company-profile p')?.textContent,sections:Array.from(document.querySelectorAll('main > section h2')).map(e=>e.textContent),printPages:document.querySelectorAll('#company-print .print-page').length,score:document.querySelector('.score-kpi strong')?.textContent,error:document.querySelector('.error')?.textContent,body:document.body.innerText.slice(0,500)})") {[weak self] result,error in
            guard let self=self else{return}
            let text=result as? String ?? "{}"
            let data=text.data(using:.utf8)!
            let json=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] ?? [:]
            if (json["charts"] as? Int)==4 || Date().timeIntervalSince(self.testStart)>160 {
                if let output=self.testOutput { try? text.write(toFile:output,atomically:true,encoding:.utf8)
                    let config=WKSnapshotConfiguration();config.rect=self.webView.bounds
                    self.webView.takeSnapshot(with:config){image,_ in
                        if let image=image,let tiff=image.tiffRepresentation,let bmp=NSBitmapImageRep(data:tiff),let png=bmp.representation(using:.png,properties:[:]) {try? png.write(to:URL(fileURLWithPath:output+".png"))}
                        if CommandLine.arguments.contains("--controls-test"){self.testControls(output)}else if CommandLine.arguments.contains("--studio-test"){self.testStudio(output)}else{self.saveSmokePDF(output)}
                    }
                }else{NSApp.terminate(nil)}
            }else{DispatchQueue.main.asyncAfter(deadline:.now()+1){self.checkSmoke()}}
        }
    }
}
let application=NSApplication.shared
let delegate=AppDelegate()
application.delegate=delegate
withExtendedLifetime(delegate) { application.run() }
