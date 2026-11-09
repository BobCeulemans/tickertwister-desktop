# Build from source

Supported release target: **Apple Silicon, macOS 14+**. Install Xcode Command Line Tools (`xcode-select --install`), Node 22+ with npm and Python 3.14. Clone the repository or unpack the corresponding source archive, then work from its root.

## App and checks

```sh
npm ci
npm test
npm run check:locales
npm run check:release
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-engine.txt
.venv/bin/python -m pytest engine/test_engine.py engine/test_data_contract.py tests/test_source.py tests/test_notarize.py
swiftc -swift-version 5 Sources/ProfileStore.swift tests/ProfileStoreTests.swift -o /tmp/tickertwister-profile-tests
/tmp/tickertwister-profile-tests
BUILD_PYTHON="$PWD/.venv/bin/python" npm run build
```

The result is `dist/Tickertwister Desktop.app`. Without `BUILD_PYTHON`, the build creates a temporary Python environment and installs the pinned requirements. A prepared environment makes rebuilding possible offline once npm and Python dependencies are installed. No sibling project or author-specific path is needed.

The build uses AppKit/WebKit/PDFKit and PyInstaller, includes the React interface and Python engine, then applies an ad-hoc signature. Check with `codesign --verify --deep --strict 'dist/Tickertwister Desktop.app'`. This does not mean Apple has notarized the app. For a Developer ID build and Apple notarization, follow [NOTARIZATION.md](NOTARIZATION.md). That workflow requires the maintainer’s own Apple Developer membership, signing identity and Keychain credential profile.

## PDF guides

```sh
python3.14 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
.venv-docs/bin/python scripts/manual.py
```

This rebuilds all seven guides using local assets and the Arial/Georgia fonts supplied with macOS. The source text is in `scripts/manuals/`. These system fonts are not distributed as standalone files. Review every PDF page visually after content changes; `pdftoppm` (Poppler) can render them. The app build packages the reviewed PDFs; it does not silently rewrite them.

## DMG and source archive

```sh
python3.14 -m venv .venv-dmg
.venv-dmg/bin/python -m pip install -r requirements-dmg.txt
bash scripts/package-dmg.sh 'dist/Tickertwister Desktop.app' 'dist/Tickertwister-Desktop-1.0.4-macOS-arm64.dmg' "$PWD/.venv-dmg/bin/python"
python3 scripts/source.py dist/Tickertwister-1.0.4-source.zip
```

The source exporter uses an explicit allowlist, refuses symlinks in source directories and excludes caches, dependencies, local profiles and developer working files. The archive includes all build scripts, editable source, dependency pins, guides and notices. Check the contents before distribution; pattern scanning is not a guarantee that a file contains no private information.

## CI

The workflow checks the code and builds the app on an Apple Silicon macOS runner. It does not publish releases or call Yahoo/OpenAI. GitHub runs it only after the repository is pushed. Native profile tests use temporary test data and do not access a real Keychain entry unless explicitly requested.
