# Apple signing and notarization

Release v1.0.4 introduces Developer ID distribution. The official DMG may be published as notarized only after every check below passes for that exact artifact. Earlier v1.0.1/v1.0.3 packages remain ad-hoc signed and not notarized. Signing the source or an earlier build does not notarize a later build.

## Prerequisites

1. Schrijf je in voor het [Apple Developer Program](https://developer.apple.com/help/account/membership/program-enrollment/) met je eigen Apple Account en tweefactorauthenticatie. Apple vermeldt 99 USD per jaar of de lokale prijs bij inschrijving. Een gewoon GitHub-account of gratis Apple Account volstaat niet.
2. Maak na activering een **Developer ID Application**-certificaat aan via Xcode of Certificates, Identifiers & Profiles. Bewaar certificaat én privésleutel in de macOS-sleutelhanger. Voor deze DMG is geen Developer ID Installer-certificaat nodig; dat laatste is voor ondertekende installatiepakketten (.pkg).
3. Maak een app-specifiek wachtwoord voor je Apple Account en sla de notarisatiegegevens via het interactieve commando hieronder op in de sleutelhanger. Deel geen wachtwoord, .p12/.p8-bestand of privésleutel in een chat of repository.
4. Bouw opnieuw met Developer ID, laat Apple de app en DMG controleren en voeg de tickets toe. Alleen het gecontroleerde eindbestand wordt daarna op GitHub aangeboden. Distributie via de Mac App Store is hiervoor niet nodig.

Notarisatie is een geautomatiseerde controle op bekende malware en ondertekeningsproblemen, geen App Store-review of garantie dat software foutloos is. Gatekeeper kan na een download nog een normale bevestiging tonen. Schakel Gatekeeper niet uit.

## Prepare the Mac

Use the tools and pinned environments in [BUILDING.md](BUILDING.md). After creating the certificate, confirm that the identity includes its private key:

```sh
security find-identity -v -p codesigning
xcrun notarytool store-credentials "tickertwister-notary"
```

If the identity is present but not valid, check its expiry, private key and Apple certificate chain. For a G2 Developer ID certificate, the official [Developer ID G2 intermediate](https://www.apple.com/certificateauthority/) may need to be installed in the login Keychain. Use Apple’s normal trust chain; do not override certificate trust.

The second command prompts for credentials and validates them with Apple. Use the Developer Program Team ID and an app-specific password, not the normal Apple Account password. The script only receives the Keychain profile name. Do not pass passwords on the command line or commit credential files. Back up the signing identity securely outside this repository.

## Build with Developer ID

Set the exact certificate name shown by `security find-identity`, including its Team ID:

```sh
export DEVELOPER_ID_APPLICATION='Developer ID Application: YOUR NAME (YOURTEAMID)'
BUILD_PYTHON="$PWD/.venv/bin/python" bash scripts/build.sh 'dist-signed/Tickertwister Desktop.app'
```

The build first checks that the identity exists. PyInstaller signs the embedded Python engine, extensions and libraries with Developer ID, hardened runtime and secure timestamps. The Swift app is signed last. The preflight verifies all Mach-O signatures and checks that they belong to the same team. An unavailable identity stops the build; it never silently switches a requested Developer ID build to ad-hoc signing.

Run the built app and smoke tests before submitting. The release uses no permissive signing entitlements by default. If Apple reports a problem, inspect the exact failing component rather than disabling library validation or re-signing everything with `--deep`.

## Submit, staple and validate

```sh
python3 scripts/notarize.py \
  --app 'dist-signed/Tickertwister Desktop.app' \
  --output 'dist-signed/Tickertwister-Desktop-1.0.4-macOS-arm64-notarized.dmg' \
  --keychain-profile 'tickertwister-notary' \
  --dmg-python "$PWD/.venv-dmg/bin/python"
```

This copies the app to a temporary staging folder, submits its ZIP, requires **Accepted**, staples and validates the ticket on the app, builds and signs the DMG, submits it, then staples and validates the DMG. Gatekeeper assessments must also pass. The supplied app is left unchanged. The final output filename is created only after all checks pass; existing output files are never overwritten.

Submission IDs, responses and Apple logs are saved in a sibling `*-notary-logs` directory. A timeout or rejection stops without retrying or publishing. If a request is still processing, inspect that same submission before deciding to submit again:

```sh
xcrun notarytool info SUBMISSION_ID --keychain-profile 'tickertwister-notary'
xcrun notarytool log SUBMISSION_ID --keychain-profile 'tickertwister-notary'
```

Do not publish logs without checking for account metadata and local paths. Do not modify the accepted app or DMG afterwards. Generate SHA-256 checksums from the final stapled DMG, download the published asset, compare its hash and test installation on another Mac. Update release notes and installation guidance with the actual signing/notarization status before the final build.

## References

- [Apple: notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [Apple: Developer ID distribution outside the Mac App Store](https://developer.apple.com/developer-id/)
- [Apple: resolving common notarization issues](https://developer.apple.com/documentation/security/resolving-common-notarization-issues)
- [PyInstaller: macOS signing](https://pyinstaller.org/en/stable/feature-notes.html#macos-specific-options)
