# Tickertwister Desktop - Financial Research Studio v1.0.3

## Changes

- Bundled yfinance upgraded from 0.2.66 to 1.8.0, with lxml 6.1.3 pinned and its notices included.
- Added regression checks for all 56 statement bindings and 31 legacy aliases. Values are matched to item names and fiscal dates, never statement row positions.
- Fixed a pre-existing EPS date-order dependency exposed by shuffled-column tests. Duplicate statement names/dates are now excluded as unavailable rather than chosen arbitrarily.
- All 39 scoring criteria, original weights, financial formulas and valuation models are retained. Historical FCFE CAGR remains the editable starting growth introduced in v1.0.2. Saved analyses and personal weights are preserved.
- Seven illustrated guides and corresponding source are included.

## Validation

AAPL, MSFT, ASML.AS and SONY were fetched with both yfinance versions on 8 November 2026. Annual and quarterly mapped values, original annual tables and all criterion contributions matched exactly in those snapshots. Independently replaying identical captured inputs and a synthetic fixture also produced identical scores, histories and valuations. See [the data migration report](docs/YFINANCE-1.8.0.md) for scope and limitations.

Existing snapshots remain unchanged. Use a fresh analysis or refresh a dossier company to retrieve new data. Yahoo can revise figures or omit data at any time; unchanged formulas do not guarantee unchanged future scores.

## Distribution status

Apple Silicon, macOS 14+. This local community build is ad-hoc signed and **NOT notarized by Apple**. Developer enrollment is pending; no Developer ID signing identity is installed yet. The signing/notarization workflow is prepared; see [NOTARIZATION.md](docs/NOTARIZATION.md).

The bundle ID and saved-data schemas are unchanged. API calls remain optional and paid only on explicit request. No AI requests are made by these upgrade tests. Financial data/service rights remain separate from the AGPLv3 source license.
