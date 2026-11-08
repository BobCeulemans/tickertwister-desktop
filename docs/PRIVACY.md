# Privacy and storage

Tickertwister is a local desktop app. It has no hosted user-account service, email registration, telemetry dashboard or automatic cloud synchronization. Local profiles are separate app profiles on the same Mac, not online accounts.

## Local data

Password-protected profile dossiers and AI archives are encrypted. Optional API-key persistence uses macOS Keychain; the key is not part of exported source or the financial prompt. Session-only use is also possible. There is no server password reset. Keep secure backups and remember your password.

Guest/legacy storage, exported analyses, printed PDFs and earlier backups may be unencrypted. Protect those separately. Encryption does not protect an unlocked session against someone using your Mac or malware. Removing a company from the study list does not automatically remove archived paid AI responses; review your archive separately.

## Network access

- **Yahoo Finance / yfinance:** requested ticker data and related market/currency information. The provider can observe requests and your network address. Notes are not sent.
- **Company websites:** logo retrieval can contact a company’s website. External links open separately and have their own privacy policies.
- **OpenAI API:** only on explicit user request and consent. The input preview shows the financial payload. Personal notes and complete dossier files are excluded. The key authenticates the API request; it is not inserted into the model prompt. Responses use `store:false`; OpenAI’s applicable API data policy still governs processing/retention.

AI output and its financial-input snapshot are saved locally. Changing app language does not translate or delete a paid response. Translation through the API is another explicit paid request. Model availability, charges and external terms can change.

For privacy-sensitive bug reports, reproduce with synthetic fixtures rather than attaching your dossier. No author credential is bundled with the app.
