#!/usr/bin/env bash
# Build Debian (.deb) package for Object Storage Bridge (OSB)
set -euo pipefail

VERSION="${1:-1.0.0}"
ARCH="amd64"
PKG_NAME="osb_${VERSION}_${ARCH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Building OSB Linux Standalone Binary ==="
cd "$ROOT_DIR"
pyinstaller osb.spec --clean --noconfirm

echo "=== Assembling Debian Package Directory ==="
PKG_DIR="$ROOT_DIR/build/deb_pkg"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

# 1. Copy executable
cp "$ROOT_DIR/dist/osb" "$PKG_DIR/usr/bin/osb"
chmod 755 "$PKG_DIR/usr/bin/osb"

# 2. Copy icon
if [ -f "$ROOT_DIR/assets/icon.png" ]; then
    cp "$ROOT_DIR/assets/icon.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/osb.png"
fi

# 3. Write DEBIAN control file
cat <<EOF > "$PKG_DIR/DEBIAN/control"
Package: osb
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Object Storage Bridge Team <info@bdata.com.mm>
Description: OSB - Enterprise GUI for Object Storage (S3, MinIO, Ceph, RustFS)
 Modern enterprise monochrome GUI for managing and transferring data across
 heterogeneous object storage servers, powered by rclone and compliant with
 NASA JPL The Power of 10 safety rules.
EOF

# 4. Write Desktop entry
cat <<EOF > "$PKG_DIR/usr/share/applications/osb.desktop"
[Desktop Entry]
Name=OSB - Object Storage Bridge
Comment=Enterprise Object Storage Manager
Exec=/usr/bin/osb
Icon=osb
Terminal=false
Type=Application
Categories=Utility;Network;FileTransfer;
StartupNotify=true
EOF

echo "=== Generating ${PKG_NAME}.deb ==="
dpkg-deb --build --root-owner-group "$PKG_DIR" "$ROOT_DIR/dist/${PKG_NAME}.deb"

echo "=== Creating tar.gz archive ==="
tar -czvf "$ROOT_DIR/dist/osb-linux-x86_64.tar.gz" -C "$ROOT_DIR/dist" osb

echo "=== Linux Build Complete ==="
ls -lh "$ROOT_DIR/dist"
