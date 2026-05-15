#!/usr/bin/env bash
# Build ckpt as a single binary using PyInstaller
# Run on each target OS: Linux, macOS, Windows (WSL2)

set -e

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install click rich pyinstaller

echo "==> Building binary..."
pyinstaller ckpt.spec --clean --noconfirm

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

BINARY="dist/ckpt"
OUTPUT="dist/ckpt-${OS}-${ARCH}"

mv "$BINARY" "$OUTPUT"
echo "==> Done: $OUTPUT"
echo "    Size: $(du -sh $OUTPUT | cut -f1)"
echo ""
echo "    Install: sudo cp $OUTPUT /usr/local/bin/ckpt"
