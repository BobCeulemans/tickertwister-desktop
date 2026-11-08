# Security policy

Security fixes initially target the latest public 1.0.x release. This is a community project without a guaranteed response time.

Do not post credentials, private dossiers, exploit details or unredacted logs in a public issue. Use GitHub’s **Security > Advisories > Report a vulnerability** for this repository when private vulnerability reporting is enabled. If it is unavailable, open a minimal issue requesting a private reporting channel without disclosing the vulnerability.

Include the app/macOS versions, affected component, impact and reproducible steps using dummy data. Never send your API key or account password. Revoke a credential exposed in a report.

Local profiles use password-derived encryption, and optional API-key persistence uses macOS Keychain. This is not protection against malware running as your user, a compromised operating system, an unlocked session or unencrypted exports/legacy backups. Losing your local password can make profile data inaccessible. See [privacy and storage](docs/PRIVACY.md).

Maintainers: enable GitHub private vulnerability reporting and secret scanning where available before public launch. Keep dependency updates reviewed, run regression tests and replace release assets only via a new tagged release.
