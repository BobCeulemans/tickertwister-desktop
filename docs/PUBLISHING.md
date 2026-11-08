# Publish v1.0.1 on GitHub

Target account: **bobceulemans**. Recommended separate repository: **tickertwister-desktop**. Display title: **Tickertwister Desktop - Financial Research Studio**. Keep the earlier Flask repository intact; add a link from its README to the new desktop project when desired.

1. Create `bobceulemans/tickertwister-desktop` as an empty repository (no generated README or license). Upload/push the prepared source directory, not the parent workspace or private research data. Use a private repository first if you want to review the GitHub rendering before launch.
2. Set the description to “Financial Research Studio for macOS: company screening, valuation and private investment research”. Add relevant topics such as `macos`, `value-investing`, `financial-analysis`, `yfinance`, `swift`, `react`, `agpl-3-0`.
3. Enable Issues, Actions and private vulnerability reporting. Run CI and inspect its results. Review the README, all guides, source license and third-party notices.
4. Commit with your own Git identity, push `main`, then create annotated tag `v1.0.1`. Do not force-push an existing project or rewrite its history.
5. Create a GitHub Release for `v1.0.1`, titled **Tickertwister Desktop - Financial Research Studio v1.0.1**. Use `RELEASE-NOTES.md` as the release body.
6. Attach the DMG, corresponding-source ZIP, all seven PDF guides and `SHA256SUMS.txt`. GitHub’s automatically generated source archives are useful too; keep the explicit source ZIP that accompanies the binary.
7. Make the repository/release public when the checks are complete. Download the published DMG and verify its checksum. Check that the release links and source download work without signing in.

Example commands from the prepared source directory, after authenticating Git with GitHub and configuring your name/email:

```sh
git init -b main
git add .
git diff --cached --stat
git commit -m "Initial public release v1.0.1"
git remote add origin https://github.com/bobceulemans/tickertwister-desktop.git
git push -u origin main
git tag -a v1.0.1 -m "Tickertwister Desktop - Financial Research Studio v1.0.1"
git push origin v1.0.1
```

Do not repeat `git init` or add a duplicate remote if already prepared. GitHub Desktop can perform the same steps without the command line. Never put a GitHub token into a repository URL, script or chat. Keep the release’s ad-hoc-signing/notarization disclosure visible. Financial-data permissions are separate from source-code licensing; see README and NOTICE.
