// SPDX-License-Identifier: AGPL-3.0-only
import AppKit
import UniformTypeIdentifiers

extension AppDelegate {
    func recoverResearchTransfer() throws {
        let url=try researchURL()
        guard FileManager.default.fileExists(atPath:url.appendingPathExtension("import-pending").path) else {return}
        try ResearchImportStorage(dossier:url,archive:aiArchiveURL(),read:readPrivate,write:writePrivate).recover()
    }

    private func transferPassword(export: Bool) throws -> String? {
        let alert=NSAlert(), tr={ (key: String) in Localization.text(key) }
        alert.messageText=tr("Transfer password")
        alert.informativeText=tr(export ? "Choose at least 12 characters. Use this password to import this file on another Mac." : "Enter the password chosen when this dossier was exported.")
        let stack=NSStackView();stack.orientation = .vertical;stack.spacing=8
        let password=NSSecureTextField(),confirmation=NSSecureTextField()
        password.placeholderString=tr("Transfer password")
        confirmation.placeholderString=tr("Confirm password")
        for field in export ? [password,confirmation] : [password] {
            field.useWorkspaceInputColors()
            stack.addArrangedSubview(field);field.widthAnchor.constraint(equalToConstant:340).isActive=true
        }
        stack.frame=NSRect(origin:.zero,size:stack.fittingSize)
        alert.accessoryView=stack;alert.window.initialFirstResponder=password
        alert.addButton(withTitle:tr(export ? "Export dossier" : "Import dossier"));alert.addButton(withTitle:tr("Cancel"))
        guard alert.runModal() == .alertFirstButtonReturn else {return nil}
        let value=password.stringValue
        defer {password.stringValue="";confirmation.stringValue=""}
        if export && (value.count<12 || value != confirmation.stringValue) {throw DossierTransfer.failure("TRANSFER_PASSWORD")}
        return value
    }

    func transferAction(_ action:String,_ body:[String:Any],_ id:Int) {
        do {
            let url=try researchURL(), manager=FileManager.default
            let type=UTType(filenameExtension:"ttdossier") ?? .data
            switch action {
            case "ai-archive-delete":
                guard let key=body["recordID"] as? String,ProfileStore.isValidID(key) else {throw DossierTransfer.failure("INVALID_ARCHIVE")}
                let record=try aiArchiveURL().appendingPathComponent(key+".json")
                if manager.fileExists(atPath:record.path) {try manager.removeItem(at:record)}
                reply(id,true,["deleted":true])
            case "research-import-apply":
                guard let content=body["content"] as? String,let revision=body["revision"] as? String else {throw DossierTransfer.failure("INVALID_TRANSFER")}
                let storage=ResearchImportStorage(dossier:url,archive:try aiArchiveURL(),read:readPrivate,write:writePrivate)
                try storage.apply(Data(content.utf8),expectedRevision:revision)
                reply(id,true,["imported":true])
            case "research-export":
                guard let content=body["content"] as? String else {throw DossierTransfer.failure("INVALID_TRANSFER")}
                let panel=NSSavePanel();panel.allowedContentTypes=[type];panel.nameFieldStringValue="Tickertwister.ttdossier"
                panel.title=Localization.text("Export dossier"); panel.canCreateDirectories=true
                guard panel.runModal() == .OK,let target=panel.url,let password=try transferPassword(export:true) else {reply(id,true,["cancelled":true]);return}
                let encrypted=try DossierTransfer.encrypt(Data(content.utf8),password:password,store:profiles)
                try encrypted.write(to:target,options:.atomic)
                reply(id,true,["saved":true])
            case "research-import-open":
                let panel=NSOpenPanel();panel.allowedContentTypes=[type];panel.allowsMultipleSelection=false;panel.canChooseDirectories=false
                panel.title=Localization.text("Import dossier")
                guard panel.runModal() == .OK,let source=panel.url else {reply(id,true,["cancelled":true]);return}
                let resource=try source.resourceValues(forKeys:[.fileSizeKey,.isRegularFileKey])
                guard resource.isRegularFile==true,let size=resource.fileSize,size<DossierTransfer.maxBytes else {throw DossierTransfer.failure("TRANSFER_SIZE")}
                guard let password=try transferPassword(export:false) else {reply(id,true,["cancelled":true]);return}
                let data=try DossierTransfer.decrypt(Data(contentsOf:source),password:password,store:profiles)
                guard let content=String(data:data,encoding:.utf8) else {throw DossierTransfer.failure("INVALID_TRANSFER")}
                reply(id,true,["content":content,"revision":try DossierTransfer.revision(url)])
            default: throw DossierTransfer.failure("INVALID_TRANSFER")
            }
        }catch {reply(id,false,["error":error.localizedDescription])}
    }
}
