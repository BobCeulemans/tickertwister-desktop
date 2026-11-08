#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail
# Arguments: app bundle, output dmg, Python with pillow/ds-store/mac-alias installed.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$1"; OUT="$2"; PYTHON="${3:-python3}"
mkdir -p "$(dirname "$OUT")"
VERSION=$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$APP/Contents/Info.plist")
STAGE=$(mktemp -d /tmp/tickertwister-dmg.XXXXXX)
mkdir "$STAGE/content" "$STAGE/content/Documentatie"
ditto "$APP" "$STAGE/content/Tickertwister Desktop.app"
ln -s /Applications "$STAGE/content/Applications"
cp "$ROOT/LICENSE" "$ROOT/NOTICE" "$ROOT/TRANSLATING.md" "$ROOT/RELEASE-NOTES.md" "$ROOT/Handleiding.html" "$ROOT/Handleiding.pdf" "$ROOT"/User-Guide-*.pdf "$STAGE/content/Documentatie/"
cp "$APP/Contents/Resources/Source/Tickertwister-source.zip" "$STAGE/content/Documentatie/"
hdiutil create -volname "Tickertwister Desktop $VERSION" -srcfolder "$STAGE/content" -fs HFS+ -format UDRW "$STAGE/layout.dmg"
# Use the normal /Volumes mount point: the background alias must identify its volume.
hdiutil attach -readwrite -nobrowse "$STAGE/layout.dmg"
VOLUME="/Volumes/Tickertwister Desktop $VERSION"
"$PYTHON" "$ROOT/scripts/dmg-layout.py" "$VOLUME"
hdiutil detach "$VOLUME"
hdiutil convert "$STAGE/layout.dmg" -format UDZO -o "$OUT"
hdiutil verify "$OUT"
