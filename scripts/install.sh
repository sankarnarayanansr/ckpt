#!/usr/bin/env sh
# curl -fsSL https://ckpt.sh/install | sh
# Detects OS and architecture, downloads the right binary

set -e

REPO="https://github.com/yourname/ckpt/releases/latest/download"
INSTALL_DIR="/usr/local/bin"
BINARY="ckpt"

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalise arch names
case "$ARCH" in
    x86_64)  ARCH="x86_64" ;;
    arm64)   ARCH="arm64"  ;;
    aarch64) ARCH="arm64"  ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    linux | darwin) ;;
    *)
        echo "Unsupported OS: $OS. Use WSL2 on Windows."
        exit 1
        ;;
esac

URL="${REPO}/ckpt-${OS}-${ARCH}"
TMP=$(mktemp)

echo "==> Downloading ckpt for ${OS}/${ARCH}..."
curl -fsSL "$URL" -o "$TMP"
chmod +x "$TMP"

echo "==> Installing to ${INSTALL_DIR}/ckpt ..."
if [ -w "$INSTALL_DIR" ]; then
    mv "$TMP" "${INSTALL_DIR}/${BINARY}"
else
    sudo mv "$TMP" "${INSTALL_DIR}/${BINARY}"
fi

echo "==> Done. Run: ckpt --version"
