// SPDX-License-Identifier: AGPL-3.0-only
import AppKit
import SwiftUI
import Translation
import UniformTypeIdentifiers

private let priceIntervals = [
    "1d": "5m", "5d": "30m", "1mo": "1d", "3mo": "1d", "6mo": "1d", "ytd": "1d",
    "1y": "1d", "2y": "1wk", "5y": "1wk", "10y": "1mo", "max": "1mo"
]

@available(macOS 15, *)
private struct LocalTranslation: View {
    let target: Locale.Language
    let text: String
    let finish: @MainActor (String?) -> Void
    var body: some View {
        Color.clear.translationTask(source: Locale.Language(identifier: "en"), target: target) { session in
            let response = try? await session.translate(text)
            await MainActor.run { finish(response?.targetText) }
        }
    }
}

extension AppDelegate {
    @MainActor
    func translateBusiness(_ body: [String: Any], id: Int) {
        guard let original = body["text"] as? String, !original.isEmpty, original.count <= 30000,
              let code = body["language"] as? String, Localization.languages.contains(code), code != "en"
        else { reply(id, false, ["error": "TRANSLATION_UNAVAILABLE"]); return }
        guard #available(macOS 15, *) else { reply(id, true, ["status": "unsupported"]); return }
        let target = Locale.Language(identifier: code)
        Task { @MainActor [self] in
            let status = await LanguageAvailability().status(from: Locale.Language(identifier: "en"), to: target)
            guard status != .unsupported else { reply(id, true, ["status": "unsupported"]); return }
            guard status == .installed || body["download"] as? Bool == true else {
                reply(id, true, ["status": "download"]); return
            }
            // The SwiftUI session lets macOS request user permission for missing language packs.
            let container = NSView(frame: NSRect(x: 0, y: 0, width: 1, height: 1))
            let host = NSHostingView(rootView: LocalTranslation(target: target, text: original) { [weak self, weak container] result in
                guard let container, container.superview != nil else { return }
                container.removeFromSuperview()
                if let result, !result.isEmpty { self?.reply(id, true, ["status": "translated", "text": result]) }
                else { self?.reply(id, true, ["status": "unavailable"]) }
            })
            host.frame = container.bounds
            container.addSubview(host)
            webView.addSubview(container)
        }
    }

    func tickerFile(_ id: Int) {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.plainText]
        panel.allowsMultipleSelection = false
        guard panel.runModal() == .OK, let url = panel.url else { reply(id, true, ["cancelled": true]); return }
        do {
            let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize
            guard let size, size <= 131072 else { throw CocoaError(.fileReadTooLarge) }
            let data = try Data(contentsOf: url)
            guard data.count <= 131072, var text = String(data: data, encoding: .utf8) else { throw CocoaError(.fileReadInapplicableStringEncoding) }
            if text.first == "\u{feff}" { text.removeFirst() }
            reply(id, true, ["text": text])
        } catch { reply(id, false, ["error": "INVALID_TICKER_FILE"]) }
    }

    func marketTool(_ action: String, body: [String: Any], id: Int) {
        guard let ticker = body["symbol"] as? String,
              ticker.range(of: "^[A-Z0-9^][A-Z0-9.^=-]{0,19}$", options: .regularExpression) != nil
        else { reply(id, false, ["error": "INVALID_TICKER"]); return }
        if action == "open-stocks" {
            let link = URL(string: "https://stocks.apple.com")!.appendingPathComponent("symbol").appendingPathComponent(ticker)
            guard let app = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.apple.stocks") else {
                reply(id, NSWorkspace.shared.open(link), ["url": link.absoluteString]); return
            }
            NSWorkspace.shared.open([link], withApplicationAt: app, configuration: NSWorkspace.OpenConfiguration()) { _, error in
                DispatchQueue.main.async { self.reply(id, error == nil || NSWorkspace.shared.open(link), ["url": link.absoluteString]) }
            }
            return
        }
        guard let range = body["period"] as? String, let interval = priceIntervals[range] else {
            reply(id, false, ["error": "INVALID_PRICE_PERIOD"]); return
        }
        var url = URLComponents(url: URL(string: "https://query1.finance.yahoo.com/v8/finance/chart")!.appendingPathComponent(ticker), resolvingAgainstBaseURL: false)!
        url.queryItems = [URLQueryItem(name: "range", value: range), URLQueryItem(name: "interval", value: interval)]
        var request = URLRequest(url: url.url!)
        request.timeoutInterval = 12
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("Tickertwister Desktop/1.1 (personal financial research)", forHTTPHeaderField: "User-Agent")
        session.dataTask(with: request) { data, response, _ in
            let http = response as? HTTPURLResponse
            let points = http?.statusCode == 200 && http?.url?.host == "query1.finance.yahoo.com" ? data.flatMap(Self.pricePoints) : nil
            DispatchQueue.main.async {
                if let points { self.reply(id, true, points) }
                else { self.reply(id, false, ["error": "PRICE_UNAVAILABLE"]) }
            }
        }.resume()
    }

    static func pricePoints(_ data: Data) -> [String: Any]? {
        guard data.count <= 2_000_000, let root = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let chart = root["chart"] as? [String: Any], let result = (chart["result"] as? [[String: Any]])?.first,
              let times = result["timestamp"] as? [Int], let indicators = result["indicators"] as? [String: Any],
              let quotes = (indicators["quote"] as? [[String: Any]])?.first, let close = quotes["close"] as? [Any],
              times.count == close.count, times.count <= 10000 else { return nil }
        let meta = result["meta"] as? [String: Any]
        var points = [[Double]]()
        for (timestamp, raw) in zip(times, close) {
            guard timestamp > 0, let value = raw as? NSNumber, value.doubleValue.isFinite else { continue }
            points.append([Double(timestamp), value.doubleValue])
        }
        guard !points.isEmpty else { return nil }
        return ["points": points, "currency": meta?["currency"] as? String ?? "", "zone": (meta?["exchangeTimezoneName"] as? String).flatMap(TimeZone.init(identifier:))?.identifier ?? "UTC"]
    }
}
