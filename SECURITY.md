# Security policy

Security fixes initially target the latest public 1.0.x release. This is a community project without a guaranteed response time.

Do not post credentials, private dossiers, exploit details or unredacted logs in a public issue. Use GitHub’s **Security > Advisories > Report a vulnerability** for this repository when private vulnerability reporting is enabled. If it is unavailable, open a minimal issue requesting a private reporting channel without disclosing the vulnerability.

Include the app/macOS versions, affected component, impact and reproducible steps using dummy data. Never send your API key or account password. Revoke a credential exposed in a report.

Local profiles use password-derived encryption, and optional API-key persistence uses macOS Keychain. This is not protection against malware running as your user, a compromised operating system, an unlocked session or unencrypted exports/legacy backups. Losing your local password can make profile data inaccessible. See [privacy and storage](docs/PRIVACY.md).

## Automated security checks

Dependabot alerts and security updates are enabled in the GitHub repository settings. Security updates propose pull requests for vulnerable dependencies; automatic merging is disabled. Review these changes and run the existing regression tests, including the financial data-contract tests, before merging. Routine version-update pull requests are not configured.

The [CodeQL workflow](.github/workflows/codeql.yml) scans Python, JavaScript/TypeScript and Swift with the security-extended query suite on pushes to `main`, version tags, pull requests targeting `main`, and weekly. It can also be started manually. Swift analysis uses the native compiler command from `scripts/build.sh` on macOS; Python and JavaScript analysis run on Linux. All three language jobs must finish successfully and upload their results. Use this advanced workflow rather than enabling a second CodeQL default setup.

Review findings under **Security > Code scanning** and **Security > Dependabot**. These checks detect possible security problems; they do not establish that financial calculations, data mappings or valuations are correct. Keep private vulnerability reporting and secret scanning enabled. Keep dependency updates reviewed, run regression tests and replace release assets only via a new tagged release.
