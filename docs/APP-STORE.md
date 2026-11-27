# Mac App Store distribution

The Store edition uses App Sandbox and a signed installer package for App Store Connect. The Developer ID disk image follows the separate [notarization process](NOTARIZATION.md).

## App record

In **App Store Connect → Apps → + → New App**, select macOS, the explicit bundle ID `be.bobceulemans.tickertwister.desktop`, a primary language and a unique internal SKU. The proposed listing name is **Tickertwister Desktop**, subtitle **Financial Research Studio**, version **1.1.0**. Apple limits the name and subtitle to 30 characters each. The Account Holder, Admin or App Manager can create this first record on the website. The Account Holder accepts agreements if prompted. [Apple’s app record instructions](https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app/)

## Prepare and test the sandbox build

Build the ordinary desktop app and install the pinned engine dependencies as described in the [build instructions](../README.md). Supply the same checkout and Python environment to the Store packaging script. For local testing use a new output path:

```sh
python3 scripts/appstore.py --sandbox-test \
  --app "dist/Tickertwister Desktop.app" \
  --python "/path/to/build-venv/bin/python" \
  --output "dist/Tickertwister Sandbox Test.app"
```

The local test app has its own bundle ID and storage container. The Store package has the production bundle ID. Both include the Python engine as an embedded background helper. It inherits the host sandbox. The host requests outgoing network access, user-selected file access and printing. The sandboxed edition stores its dossier inside its container. Use the existing export and import functions to transfer a dossier from a direct installation.

Check a live ticker, saving and reopening a test dossier, optional Keychain access, user-selected imports and exports, and printing. Repeat on a Store-signed build via TestFlight before public release.

## Create the installer

Install a Mac App Store application signing identity and a Mac Installer Distribution identity with their private keys. Create a Mac App Store distribution profile for the explicit bundle ID and application signing certificate. Use the names shown by `security find-identity -v -p basic`.

```sh
python3 scripts/appstore.py \
  --app "dist/Tickertwister Desktop.app" \
  --python "/path/to/build-venv/bin/python" \
  --profile "/path/to/Tickertwister.provisionprofile" \
  --identity "Apple Distribution: YOUR NAME (TEAMID)" \
  --installer "3rd Party Mac Developer Installer: YOUR NAME (TEAMID)" \
  --output "dist/Tickertwister-Desktop-App-Store.pkg"
```

The script verifies nested signatures and the package signature. Upload the package with Transporter and resolve any validation messages in App Store Connect. [Apple’s distribution packaging guide](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution) · [App Store provisioning](https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile/) · [Upload builds](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/)

## Prepare the review submission

Supply the description, screenshots, active support and privacy URLs, age rating, price and availability, review contact and review instructions. Complete App Privacy with reference to [the actual data flows](PRIVACY.md) and the current practices of all integrated providers. Confirm rights for third-party content and market data, and answer the encryption questionnaire for the shipped implementation. Select the processed build for this version and submit for App Review. Only Apple can approve the submission.
