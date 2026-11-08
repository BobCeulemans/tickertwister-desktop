// SPDX-License-Identifier: AGPL-3.0-only
import Foundation
// Shared, editable catalogs. Language changes never touch financial data or secrets.
enum Localization {
    static let languages=["nl","en","fr","de","es","it","pt"]
    static var current=UserDefaults.standard.string(forKey:"appLanguage") ?? "nl"
    static let catalogs:[String:[String:String]]=Dictionary(uniqueKeysWithValues:languages.map { code in
        let url=Bundle.main.resourceURL?.appendingPathComponent("Locales/\(code).json")
        let data=url.flatMap {try? Data(contentsOf:$0)}
        let values=data.flatMap {try? JSONSerialization.jsonObject(with:$0) as? [String:String]} ?? [:]
        return (code,values)
    })
    static func text(_ key:String,_ language:String?=nil)->String {
        catalogs[language ?? current]?[key] ?? catalogs["en"]?[key] ?? key
    }
}
