# Changelog

## 1.1.0 · 27 November 2026 (build 31)

- Redesigned workspace, regional and sector-aware valuation models, and portable encrypted research dossiers from the v1.1.0 previews.
- Remove successive companies before saving, with individual undo and restoration of notes and list order.
- Centered the Buffett and Munger quotation above ticker entry.
- Prepared the Developer ID distribution for Apple Silicon under the corrected name Bob Ceulemans.

## 1.1.0 · Preview 7 (build 30)

- Financial-company DCFs start with historical revenue growth when available. Payment networks and other non-bank financial services use a currency-matched WACC when available. Banks and insurers start with their cost of equity, which can be overridden and saved.
- Capital cost estimates display WACC to two decimals and retain calculation precision. Restore initial values reapplies the sourced assumptions.
- The opening quote precedes ticker entry. Sponsors appears above Workspace in the sidebar. The footer, batch actions, company search, selection columns and navigation cursors have been aligned.

## 1.1.0 · Preview 6 (build 29)

- Separate bank and insurer equity valuations from debt-weighted estimates for operating companies. Match the ten-year benchmark to currency and trailing statement flows to the balance date.
- Adjust financial-sector cash flows and historical growth, and disclose the three-year normalisation.
- Update dark appearance, editable fields, Quick notes, company selections, formulas, and wide-screen valuation tables.


## 1.1.0 — fifth local preview, 27 November 2026 (build 28)

- Password-encrypted selective dossier transfer and saved AI analysis deletion.
- Sequential ticker lists, analysis scratchpad, price history and Apple Stocks shortcut.
- WACC reference, explicit Owner Earnings estimates, 2% default terminal growth and source formulas.
- Python 3.14.10 bundled for local review.

## 1.1.0 — fourth local preview, 22 November 2026 (build 27)

- Preferences at sign-in, system language on first use, clearer colour and navigation controls, and local account management.
- Compact valuation summary with financial terminology preferences. The minimum discount rate is 6% or the higher recent ten-year US Treasury yield.
- Personal scoring overrides retain the original assessment. The selected company can be opened directly from the dossier list header.
- A small GitHub Sponsors link is available in the app.

## 1.1.0 — third local preview, 21 November 2026 (build 26)

- Show two automatic ten-year DCF values using historical Owner Earnings growth capped at 10% and 12%, each with a −20% floor. The primary default uses the 10% ceiling. Users can enter a separate forecast.
- Retrieve the dated ten-year constant maturity rate from the US Treasury, with FRED as a second source and a dated local cache. The 6% fallback applies below 3% or when a recent observation is unavailable.
- Updated the seven illustrated guides with the two assumptions and working-capital treatment.

## 1.1.0 — second local preview, 21 November 2026

- One ten-year Owner Earnings DCF with a dated Treasury reference, an explicit terminal value and a bridge to value per share.
- Annual tables sit beside their scoring rules. Additional histories are available in the same section.
- Compact Analysis home, Research dossier navigation, a light sign-in screen and collapsed dossier sections.

## 1.1.0 — local preview, 14 November 2026

- Stable Mac workspace with Overview, Research, Compare, Valuation and AI archive; dossier preview, profile footer and multiple open analyses.
- Owner-earnings DCF replaces the FCFE terminal-multiple model. Explicit cash-flow basis, editable expansion capex, dated Treasury reference, net-debt bridge and optional editable Gordon dividend model.
- Personalized score badges and totals, theme contrast, section alignment, financial-term translations, AI reading sizes and native menus corrected.
- Seven manuals, saved analysis handling and printed valuation reports updated.
- Local review only: no GitHub push or publication. Apple account-holder correction and release signing remain pending.


## Unreleased — local Mac interface preview

- Introduce the Focus welcome screen with the existing Buffett and Munger illustration and recent saved companies.
- Add a persistent sidebar, compact toolbar and Preferences for light, dark or system appearance, accent and language.
- Present the research dossier as a Library with company search, status filters and readable selection in both appearances.
- Keep the native window dimensions, financial formulas, weights, data formats and all research features unchanged.
- Update all seven illustrated guides with the Mac workspace and examples.
- Local preview only: no GitHub publication, Developer ID signing or notarization. The v1.0.4 publication hold remains in force.

## 1.0.4 — 2026-11-09

- Seal embedded Python framework resources before signing the outer app; verify every embedded executable before Apple submission.

- Enable Dependabot vulnerability alerts and security-update pull requests; keep automatic merging disabled.
- Add CodeQL security analysis for Python, JavaScript/TypeScript and the native Swift app on main, version tags, pull requests and a weekly schedule.
- Harden archive and profile identifier validation to require a complete UUID, with regression checks for malformed identifiers. Existing valid IDs and saved-data formats are preserved.

- Prepare Developer ID signed distribution with Apple acceptance, stapled app and DMG tickets, and Gatekeeper checks required before publishing the notarized installer. Earlier public installers remain unchanged.
- Update all seven illustrated guides and installation documentation. Keep the 39 financial criteria, weights, formulas, yfinance 1.8.0 and saved-data formats unchanged.

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
