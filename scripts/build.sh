#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo 'The supported desktop build requires an Apple Silicon Mac.' >&2; exit 1
fi
APP_DEST="${1:-$PROJECT_DIR/dist/Tickertwister Desktop.app}"
BUILD_TMP="$(mktemp -d /tmp/tickertwister-build.XXXXXX)"
APP_TMP="$BUILD_TMP/Tickertwister Desktop.app"
mkdir -p "$APP_TMP/Contents/MacOS" "$APP_TMP/Contents/Resources"
SIGNING_ARGS=(--noconfirm)
if [ -n "${DEVELOPER_ID_APPLICATION:-}" ]; then
  python3 "$PROJECT_DIR/scripts/notarize.py" --check-identity "$DEVELOPER_ID_APPLICATION"
  SIGNING_ARGS+=(--codesign-identity "$DEVELOPER_ID_APPLICATION")
fi
# BUILD_PYTHON can point to a prepared Python 3.14 environment for offline builds.
if [ -z "${BUILD_PYTHON:-}" ]; then
  python3.14 -m venv "$BUILD_TMP/venv"
  BUILD_PYTHON="$BUILD_TMP/venv/bin/python"
  "$BUILD_PYTHON" -m pip install -r "$PROJECT_DIR/requirements-engine.txt"
fi
"$BUILD_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3,14), "Python 3.14 required"'
"$BUILD_PYTHON" - <<'PY'
from importlib.metadata import version
from pathlib import Path
for line in Path('requirements-engine.txt').read_text().splitlines():
    if not line.strip() or line.startswith('#'):
        continue
    name, expected = line.split('==')
    actual = version(name)
    if actual != expected:
        raise SystemExit(f'Build dependency mismatch: {name} {actual}; expected {expected}')
print('Pinned engine dependencies verified.')
PY
"$BUILD_PYTHON" "$PROJECT_DIR/scripts/check-release.py"
# The seven reviewed PDFs are shipped in source. Regenerate deliberately with
# scripts/manual.py and visually review before a release, not on every app build.
"$BUILD_PYTHON" -m PyInstaller "${SIGNING_ARGS[@]}" --onedir --name YahooEngine --distpath "$BUILD_TMP/dist" --workpath "$BUILD_TMP/pyinstaller" --specpath "$BUILD_TMP" --add-data "$PROJECT_DIR/engine/labels.json:." --collect-all curl_cffi --collect-all yfinance --copy-metadata yfinance "$PROJECT_DIR/engine/engine.py"
ditto "$BUILD_TMP/dist/YahooEngine" "$APP_TMP/Contents/Resources/Engine"
node "$PROJECT_DIR/scripts/build.mjs" "$APP_TMP"
cp "$PROJECT_DIR/Info.plist" "$APP_TMP/Contents/Info.plist"
cp "$PROJECT_DIR/Handleiding.html" "$PROJECT_DIR/Handleiding.pdf" "$PROJECT_DIR"/User-Guide-*.pdf "$PROJECT_DIR/NOTICE" "$PROJECT_DIR/LICENSE-React.txt" "$PROJECT_DIR/LICENSE" "$PROJECT_DIR/LICENSE-Apache-2.0.txt" "$APP_TMP/Contents/Resources/"
if [ -d "$PROJECT_DIR/licenses" ]; then ditto "$PROJECT_DIR/licenses" "$APP_TMP/Contents/Resources/Licenses"; fi
swiftc -swift-version 5 -O -target arm64-apple-macos14.0 -module-cache-path "$BUILD_TMP/module-cache" "$PROJECT_DIR"/Sources/*.swift -o "$APP_TMP/Contents/MacOS/Tickertwister" -framework AppKit -framework WebKit -framework PDFKit
cp "$PROJECT_DIR/AppIcon.icns" "$APP_TMP/Contents/Resources/AppIcon.icns"
mkdir -p "$APP_TMP/Contents/Resources/Source"
cp "$PROJECT_DIR/LICENSE" "$PROJECT_DIR/NOTICE" "$PROJECT_DIR/README.md" "$APP_TMP/Contents/Resources/Source/"
python3 "$PROJECT_DIR/scripts/source.py" "$APP_TMP/Contents/Resources/Source/Tickertwister-source.zip"
if [ -n "${DEVELOPER_ID_APPLICATION:-}" ]; then
  # PyInstaller signs its collected binaries/frameworks first, with hardened
  # runtime and timestamps. Seal the outer bundle last; do not deep-sign it.
  codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID_APPLICATION" "$APP_TMP"
  python3 "$PROJECT_DIR/scripts/notarize.py" --check-app "$APP_TMP"
else
  codesign --force --deep --sign - "$APP_TMP"
  echo 'Local ad-hoc build: NOT notarized. See docs/NOTARIZATION.md.'
fi
codesign --verify --deep --strict "$APP_TMP"
mkdir -p "$(dirname "$APP_DEST")"
ditto "$APP_TMP" "$APP_DEST"
printf 'App gebouwd: %s\n' "$APP_DEST"
