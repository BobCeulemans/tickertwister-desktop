# Tickertwister Desktop - Financial Research Studio v1.0.4

## Security and distribution

- Profile and AI-archive identifiers must match a complete UUID. Malformed identifiers are rejected before use; regression tests cover suffixes, separators, newlines and null characters. Existing valid identifiers and saved-data formats remain compatible.
- Dependabot alerts and security updates are enabled, with automatic merging disabled. CodeQL checks Python, JavaScript/TypeScript and Swift. Build checks retain both main and version-tag triggers, using GitHub Actions with Node.js 24 support.
- The official installer is published only after Developer ID signing, Apple acceptance for both the app and disk image, ticket stapling and successful Gatekeeper verification. See the GitHub release for the verified status of its exact download. Locally built and CI artifacts are ad-hoc signed unless explicitly built with Developer ID; they do not inherit notarization.
- All seven illustrated guides and the complete corresponding source are included in the app, disk image and release downloads.

## Financial continuity

The 39 scoring criteria, original weights, financial formulas and valuation models are unchanged. yfinance remains pinned to 1.8.0. Historical FCFE CAGR remains the editable starting growth; saved assumptions, personal weights and research dossiers are preserved.

The v1.0.3 [data migration report](docs/YFINANCE-1.8.0.md) remains available. Live financial figures can change when Yahoo revises or refreshes its data.

## Installation

Apple Silicon, macOS 14 or newer. Download the DMG marked notarized from this repository’s Releases, open it and drag Tickertwister Desktop.app into Applications. Launch it from Applications, then eject the disk image. A normal first-open confirmation may still appear. Do not disable Gatekeeper.

Earlier v1.0.1 and v1.0.3 downloads are not notarized and are not replaced silently. A new signature or ticket applies only to the corresponding v1.0.4 download. Compare the downloaded file with SHA256SUMS.txt.

API calls remain optional and require an explicit request. No paid AI calls are part of release testing. Data and service rights remain separate from the AGPLv3 source license.
