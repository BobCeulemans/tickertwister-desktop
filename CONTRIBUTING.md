# Contributing

Thank you for helping improve Tickertwister. Start with the [build guide](docs/BUILDING.md); translation contributors should also read [TRANSLATING.md](TRANSLATING.md).

1. Open an issue describing the behavior or proposal, with synthetic or public examples.
2. Fork the repository, create a focused branch and make the change.
3. Run JavaScript, Python, native profile and locale checks relevant to the change. Explain validation in the pull request.
4. Keep formulas, units, currency and dates explicit. Never turn unavailable financial data into zero. A locale change must not alter calculations or currencies.
5. Update all affected guides/catalogs and describe any saved-data migration. Preserve existing dossiers and archive originals.

Use small, reviewable pull requests. UI changes need before/after screenshots with names, notes and account details redacted. Finance changes need worked examples and meaningful regression tests, including missing/negative inputs. Do not introduce paid network calls in automated tests.

Do not commit keys, tokens, real dossiers, AI archives, user exports, `.env` files or signing certificates. Use the security reporting process for vulnerabilities.

By contributing, you agree that your original contributions are licensed under this project’s AGPL-3.0-only license. Only submit work you are entitled to license, and preserve third-party notices. No copyright assignment is required. Dependencies and imported code need compatible licenses and retained attribution.
