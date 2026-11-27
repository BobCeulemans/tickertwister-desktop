<p align="center"><img src="web/app-icon.png" width="96" alt="Tickertwister logo"></p>

# Tickertwister Desktop - Financial Research Studio

**The Value Investor’s Notebook · v1.1.0**

A macOS desktop app for a first, evidence-based look at a listed company. Explore financial statements, 39 transparent analysis criteria, valuation scenarios and your own investment thesis in a private research workspace.

Built by **Bob Ceulemans**. Free software under **AGPL-3.0-only**.

[User guides](#user-guides) · [Build from source](docs/BUILDING.md) · [Contribute](CONTRIBUTING.md) · [Privacy](docs/PRIVACY.md) · [Release notes](RELEASE-NOTES.md) · [Support](#support-this-project) · [Nederlands](README.nl.md)

<p align="center"><img src="web/buffett-munger.png" width="440" alt="Original illustrated caricature of Warren Buffett and Charlie Munger at a research desk"></p>

## What you can do

- Fetch annual statements with yfinance and inspect up to four fiscal years in the original 39-criterion model, with data coverage and editable weights.
- Explore profitability, cash conversion, debt, historical trends and additional Buffett & Clark-inspired financial relationships, with visible formulas.
- Adjust owner-earnings DCF and optional dividend-based Gordon Growth assumptions; inspect currency-matched ten-year government yields, net debt, scenarios and sensitivity.
- Keep investment theses, research status and saved analyses; compare one to four companies using the available common periods or a clearly labelled longer-history window.
- Request optional AI-AIC interpretation through your own paid OpenAI API account.
- Use encrypted local profiles, transfer selected research between Macs in a separately password-protected .ttdossier file, and optionally store your API key in macOS Keychain.
- Print company and research reports with your chosen AI appendices.
- Choose Dutch, English, French, German, Spanish, Italian or Portuguese. App language and AI output language are independent. Optionally retain English financial terminology.

A score is a screening model, not a probability of investment success. Missing data, industry differences and accounting choices matter. The app does not place trades or provide personalized investment advice.

## Install

Download the [Tickertwister Desktop v1.1.0 release](https://github.com/BobCeulemans/tickertwister-desktop/releases/tag/v1.1.0) for **Apple Silicon, macOS 14 or later**. Choose the notarized disk image and drag **Tickertwister Desktop.app** into Applications. The **Documentatie** folder includes seven guides, licenses and the corresponding source archive. The app bundles its own financial engine.

The GitHub release lists the SHA-256 checksum for the distributed disk image. The signing identity for the direct distribution is **Developer ID Application: Bob Ceulemans**. The [signing and notarization guide](docs/NOTARIZATION.md) describes the maintainer checks.

Yahoo access needs an internet connection. Saved dossiers and local calculations can be used offline. AI is optional, requires a separate API account/key and may incur charges; a ChatGPT subscription does not supply API credit. Nothing requests AI automatically when you change a language or model.

## User guides

| Language | Illustrated PDF |
|---|---|
| Nederlands | [Handleiding](Handleiding.pdf) |
| English | [User guide](User-Guide-EN.pdf) |
| Français | [Guide](User-Guide-FR.pdf) |
| Deutsch | [Handbuch](User-Guide-DE.pdf) |
| Español | [Guía](User-Guide-ES.pdf) |
| Italiano | [Guida](User-Guide-IT.pdf) |
| Português | [Guia](User-Guide-PT.pdf) |

Dutch and English are full guides; the other five editions are concise localized guides. All are included in the app’s Help menu and every release. Independent native-speaker financial review is pending; see [translation status](TRANSLATING.md).

## Build and test

On an Apple Silicon Mac with Xcode Command Line Tools, Node 22+ and Python 3.14:

```sh
npm ci
npm test
npm run check:locales
npm run check:release
npm run build
```

The build creates `dist/Tickertwister Desktop.app`, including the Python engine, web UI, licenses, guides and corresponding source archive. It installs pinned engine dependencies into a temporary build environment. See [complete build instructions](docs/BUILDING.md) for Python/native tests, offline builds, manuals and DMG creation.

## Project layout

| Path | Purpose |
|---|---|
| `Sources/` | Swift/AppKit host, WebKit bridge, profile encryption and native dialogs |
| `web/` | React UI, financial models, reports and locale catalogs |
| `engine/` | yfinance adapter and original Python analysis rules |
| `tests/` | Financial, presentation, serialization and security regression tests |
| `scripts/` | Build, manual generation, source export and DMG packaging |
| `licenses/` | Third-party license texts |
| `docs/` | Build, financial-method, privacy and publication documentation |


## License and data rights

The application is licensed under the **GNU Affero General Public License v3.0 only**; see [LICENSE](LICENSE) and [NOTICE](NOTICE). The earlier Python analysis retains its Apache-2.0 notices. Dependencies retain their own licenses. Corresponding source is included with each binary in Help > License and source and in the DMG. Modified network-accessible versions must meet AGPL’s applicable source-offer obligations.

The software license does **not** grant rights to Yahoo financial data, company logos, trademarks or third-party services. The [yfinance project](https://github.com/ranaroussi/yfinance) identifies its code as Apache-2.0 and explains that Yahoo’s financial API is intended for personal use. Review the applicable provider terms and obtain appropriate data rights before commercial distribution or service use. This project is not affiliated with Yahoo, OpenAI, Berkshire Hathaway, Warren Buffett or Charlie Munger.

Copyright ©2026 Bob Ceulemans  
All Rights Reserved. Rights granted by the licenses above remain fully available.

## Support this project

If Tickertwister is useful to you, [support Bob Ceulemans on GitHub Sponsors](https://github.com/sponsors/BobCeulemans) to help maintain it and develop future open-source projects.

Suggested support: **$5, $10 or $25**, one-time or monthly. Choose your amount and frequency on GitHub Sponsors.

Sponsorship is entirely voluntary. The apps remain available to everyone; contributions do not purchase exclusive features, investment advice or priority support.
