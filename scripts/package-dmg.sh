#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail
# Arguments: app bundle, output dmg, Python with pillow/ds-store/mac-alias installed, optional volume name.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$1"; OUT="$2"; PYTHON="${3:-python3}"
APP_NAME="$(basename "$APP")"
mkdir -p "$(dirname "$OUT")"
VERSION=$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$APP/Contents/Info.plist")
STAGE=$(mktemp -d /tmp/tickertwister-dmg.XXXXXX)
mkdir "$STAGE/content" "$STAGE/content/Documentatie"
ditto "$APP" "$STAGE/content/$APP_NAME"
ln -s /Applications "$STAGE/content/Applications"
cp "$ROOT/LICENSE" "$ROOT/NOTICE" "$ROOT/TRANSLATING.md" "$ROOT/RELEASE-NOTES.md" "$ROOT/Handleiding.html" "$ROOT/Handleiding.pdf" "$ROOT"/User-Guide-*.pdf "$STAGE/content/Documentatie/"
cp "$APP/Contents/Resources/Source/Tickertwister-source.zip" "$STAGE/content/Documentatie/"
VOLUME_NAME="${4:-Tickertwister Desktop $VERSION}"
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$STAGE/content" -fs HFS+ -format UDRW "$STAGE/layout.dmg"
# Use the normal /Volumes mount point: the background alias must identify its volume.
hdiutil attach -readwrite -nobrowse -plist "$STAGE/layout.dmg" > "$STAGE/attached.plist"
# Finder may already have mounted another preview with this volume name.
VOLUME=$("$PYTHON" -c 'import plistlib, sys
with open(sys.argv[1], "rb") as handle:
    [mount] = [item["mount-point"] for item in plistlib.load(handle)["system-entities"] if "mount-point" in item]
print(mount)' "$STAGE/attached.plist")
trap 'hdiutil detach "$VOLUME" >/dev/null' EXIT
"$PYTHON" "$ROOT/scripts/dmg-layout.py" "$VOLUME" "$APP_NAME"
hdiutil detach "$VOLUME"
trap - EXIT
hdiutil convert "$STAGE/layout.dmg" -format UDZO -o "$OUT"
hdiutil verify "$OUT"
