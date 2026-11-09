# Publish a release on GitHub

Repository: **https://github.com/BobCeulemans/tickertwister-desktop**. Display title: **Tickertwister Desktop - Financial Research Studio**. The initial v1.0.1 release is already published. Keep the earlier Flask repository and existing tags intact.

1. Review the diff, run the checks in BUILDING.md and update the changelog, release notes, version metadata and all seven guides together. Review the rendered guides and test the native app with isolated fixtures.
2. For a notarized distribution, complete [NOTARIZATION.md](NOTARIZATION.md). Use the final accepted and stapled DMG, never an intermediate artifact. If distributing an ad-hoc build, retain the explicit **not notarized** disclosure. Prepared scripts alone do not establish Apple acceptance.
3. Build the corresponding-source ZIP from the exact sources used for the app. Attach it, the DMG, all seven PDF guides, release notes and SHA256SUMS.txt. Check the allowlist for private files and credentials before distribution.
4. Commit with the maintainer’s Git identity, push the reviewed changes and inspect CI. Create a new annotated version tag; do not overwrite a released tag or force-push history.
5. Create a release using RELEASE-NOTES.md, with the title **Tickertwister Desktop - Financial Research Studio v1.0.4** and the reviewed assets.
6. Download the published DMG, compare its checksum and test its installation. Confirm that source and guide links work without signing in.

Publishing is a separate maintainer action. Building locally does not publish or modify a GitHub release. Never put a GitHub token, Apple app-specific password or signing private key into a script, repository URL or chat. Financial-data permissions remain separate from source-code licensing; see README and NOTICE.
