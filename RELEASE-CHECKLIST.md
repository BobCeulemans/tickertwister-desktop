# Release checklist

1. Update `package.json`, lockfile and `Info.plist` together. Increase the native build number; retain bundle ID and saved-data schemas unless an explicit migration is tested.
2. Update `RELEASE-NOTES.md`, `CHANGELOG.md`, NOTICE and all affected documentation.
3. Maintain **all seven guides**. Update `scripts/manuals/nl.py`, `en.py` and `international.json`, regenerate PDFs, render every page and visually review. PDFs must match the release version.
4. Run JavaScript, Python/source-export, locale and Swift profile tests; run release validation and a native UI smoke test with synthetic data.
5. Confirm translations preserve currency, financial units and abbreviations. Record native-speaker review status honestly in TRANSLATING.md.
6. Audit the export allowlist, dependency licenses, secret-pattern scan and resulting source ZIP. Never copy user folders or a parent workspace into Git.
7. Build the app from the prepared standalone source, verify its signature, build/verify the DMG and check Documentation layout.
8. Include the matching source ZIP and seven PDFs in the app, DMG and release downloads. Generate SHA-256 checksums for release assets.
9. Enable private vulnerability reporting, run GitHub CI and review the initial public repository before publishing/tagging.
10. Download the published assets and confirm checksums. State signing/notarization and platform support accurately. Do not replace an existing public version’s binaries silently.
