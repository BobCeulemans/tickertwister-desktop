# International release · 1.0.3

Supported locales: `nl` (Belgium), `en` (US), `fr` (France), `de` (Germany), `es` (Spain), `it` (Italy), `pt` (Portugal). These locales control presentation, not the currency or jurisdiction of a company.

## Files and fallback

`web/locales/en.json` is the source catalog. The other six JSON files use the same English keys. Translate values, not keys. `web/i18n.mjs` supplies English fallback for missing/empty values and unsupported languages. `Sources/Localization.swift` loads the same catalogs from the app bundle. Never put credentials, notes or user financial data in these files.

Financial labels are also in these catalogs. Keep ticker symbols, currency codes, formula operators and abbreviations such as ROE, ROA, FCFE, CAGR and EBITDA unchanged. `financial-keys.json` identifies financial terms in legacy explanations. Source descriptions, original user notes, raw financial-input previews and archived AI text are not silently translated. Legacy/source explanations without a catalog entry use English fallback. Do not rewrite numerical scoring rules to translate their explanations.

The optional English-financial-terms setting affects terminology only. Interface buttons, dates and numbers still follow the chosen locale. Values and currency codes must remain unchanged. Translations must distinguish English billion (10^9) from trillion (10^12), and Dutch miljard from biljoen.

## AI language

The output-language control starts at Follow app language. A separately selected language persists independently. A language change does not send a request, delete an archive entry or overwrite a paid response. Explicit API translation is a new paid request and preserves the original. Each response stores its own language. Financial input/schema keys stay stable in English for reproducibility.

## Guides and reports

The maintained Dutch/English full guides live in `scripts/manuals/nl.py` and `en.py`. The five new concise localized guides are in `scripts/manuals/international.json`. All cover installation, languages, valuation, scores, research, security, AI, reports and limits. `scripts/manual.py` builds all seven PDFs by default, with one common layout. They are bundled in both the app Help menu and DMG Documentation folder. Update all editions when behavior changes. Print-report labels share the app catalogs; user notes and source company descriptions retain their original language.

## Contribution and review workflow

1. Change the English source text only if the behavior/meaning changed; update all locale files in that case.
2. Translate whole sentences, preserving formulas, placeholders, punctuation needed by concatenated labels and unit scale.
3. Run `node --test tests/*.test.mjs` and `node scripts/check-locales.mjs`.
4. Build the app and all guides. Review long labels, compact widths, native dialogs and multipage reports in the target language.
5. Ask a native speaker with financial knowledge to review terminology, caveats and number/date notation. Record the language, reviewer, date, revision and outstanding issues below.
6. Keep English fallback for unreviewed additions rather than inventing financial definitions. Never approve a translation merely because the catalog has no missing keys.

## Review status

All seven catalogs have structural coverage checks; the seven-language financial/AI invariance tests pass. The five new languages are initial translations, **not independently native-speaker certified**. Independent financial-language review is pending for every edition. Community contributions and reviewer sign-off must be tracked before labelling a locale “reviewed”.

| Language | Native financial reviewer | Revision/date | Status |
|---|---|---|---|
| nl | Pending | 1.0.3 | Review requested |
| en | Pending | 1.0.3 | Review requested |
| fr | Pending | 1.0.3 | Review requested |
| de | Pending | 1.0.3 | Review requested |
| es | Pending | 1.0.3 | Review requested |
| it | Pending | 1.0.3 | Review requested |
| pt-PT | Pending | 1.0.3 | Review requested |
