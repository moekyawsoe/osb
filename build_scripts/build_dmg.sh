#!/usr/bin/env bash
# Build macOS DMG package for Object Storage Bridge (OSB)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Building OSB macOS Application Bundle ==="
cd "$ROOT_DIR"
pyinstaller osb.spec --clean --noconfirm

echo "=== Packaging OSB into DMG Disk Image ==="
DMG_PATH="$ROOT_DIR/dist/OSB-macOS.dmg"
APP_PATH="$ROOT_DIR/dist/OSB.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH was not found!"
    exit 1
fi

# Remove old dmg if present
rm -f "$DMG_PATH"

# Create a staging directory with symlink to /Applications for Drag & Drop install
STAGE_DIR="$ROOT_DIR/build/dmg_stage"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp -R "$APP_PATH" "$STAGE_DIR/"
ln -s /Applications "$STAGE_DIR/Applications"

# Create compressed UDZO disk image using native macOS hdiutil
hdiutil create -volname "OSB" -srcfolder "$STAGE_DIR" -ov -format UDZO "$DMG_PATH"

echo "=== Creating macOS Zip Archive ==="
cd "$ROOT_DIR/dist"
zip -r "OSB-macOS.zip" "OSB.app"

echo "=== macOS Build Complete ==="
ls -lh "$ROOT_DIR/dist"
