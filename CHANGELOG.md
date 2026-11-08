# Changelog

## 1.0.3 — 2026-11-08

- Upgrade the bundled Yahoo adapter to yfinance 1.8.0; pin its new lxml dependency to 6.1.3.
- Verify statement-name/date bindings for all 56 mapped fields, yearly and quarterly data, aliases, signs and missing data.
- Align diluted EPS explicitly to fiscal dates. Reject ambiguous duplicate statement rows/dates instead of selecting arbitrary values.
- Preserve all 39 scoring rules, original weights, valuation formulas, personal settings and saved-data schemas.
- Update all seven guides and corresponding-source distribution.


## 1.0.2 — 2026-11-08

Local interim version, tested and delivered locally but not published as a separate GitHub release. Its small follow-up changes were incorporated into v1.0.3, which was already being prepared shortly afterwards. All v1.0.2 changes are included in the v1.0.3 source and installer; there is no separate public v1.0.2 download.

- Main FCFE model starts from the same historical FCFE CAGR as the Valuation Lab. Manual/saved assumptions remain editable and preserved. Missing CAGR starts at an explicitly disclosed 0%, without a revenue-growth fallback.
- Developer ID build option and fail-closed Apple notarization/stapling workflow. Requires the maintainer’s Apple Developer membership and certificates; preparation does not make an ad-hoc build notarized.
- Updated seven language catalogs and version-aligned guides.

## 1.0.1 — 2026-11-08

Initial public release of Tickertwister Desktop - Financial Research Studio. See [release notes](RELEASE-NOTES.md).

Private development used version numbers through 6.0.3. Those numbers are deliberately reset for the public project; data formats and the app bundle identifier remain unchanged.

This release adds a self-contained source build, pinned JavaScript lockfile, publication checks, contributor/security documentation and seven version-aligned guides. It preserves the tested financial and research features from the final private version.
