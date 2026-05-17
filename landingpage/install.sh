#!/usr/bin/env sh
set -e

KEY="$1"
if [ -z "$KEY" ]; then
  echo "Usage: curl -fsSL https://deltapro.site/install | sh -s -- YOUR-LICENSE-KEY"
  exit 1
fi

# ── Detect OS ──────────────────────────────────────────────────────────
RAW_OS=$(uname -s)
case "$RAW_OS" in
  Linux)  OS="linux"  ;;
  Darwin) OS="darwin" ;;
  *)
    echo "Unsupported OS: $RAW_OS"
    echo "On Windows, use WSL2 and re-run this script inside it."
    exit 1
    ;;
esac

# ── Detect arch ────────────────────────────────────────────────────────
RAW_ARCH=$(uname -m)
case "$RAW_ARCH" in
  x86_64)          ARCH="x86_64" ;;
  arm64 | aarch64) ARCH="arm64"  ;;
  *)
    echo "Unsupported architecture: $RAW_ARCH"
    exit 1
    ;;
esac

echo "==> Detected: ${OS}/${ARCH}"
echo "==> Downloading deltapro..."

TMP=$(mktemp)

# ── Download from gate ─────────────────────────────────────────────────
HTTP_CODE=$(curl -fsSL \
  --write-out "%{http_code}" \
  --output "$TMP" \
  "https://deltapro.site/get?key=${KEY}&os=${OS}&arch=${ARCH}")

if [ "$HTTP_CODE" != "200" ]; then
  echo "==> Download failed (HTTP $HTTP_CODE):"
  cat "$TMP"
  rm -f "$TMP"
  exit 1
fi

# ── Validate it looks like a real binary ───────────────────────────────
# Check ELF magic (Linux) or Mach-O magic (macOS) in first 4 bytes
MAGIC=$(dd if="$TMP" bs=1 count=4 2>/dev/null | xxd -p 2>/dev/null || true)

case "$OS" in
  linux)
    # ELF: 7f454c46
    if [ "$MAGIC" != "7f454c46" ]; then
      echo "==> Error: downloaded file does not look like a Linux binary."
      echo "    Response from server:"
      cat "$TMP"
      rm -f "$TMP"
      exit 1
    fi
    ;;
  darwin)
    # Mach-O arm64: cffaedfe  |  Mach-O x86_64: cefaedfe
    if [ "$MAGIC" != "cffaedfe" ] && [ "$MAGIC" != "cefaedfe" ]; then
      echo "==> Error: downloaded file does not look like a macOS binary."
      echo "    Response from server:"
      cat "$TMP"
      rm -f "$TMP"
      exit 1
    fi
    ;;
esac

# ── Install ────────────────────────────────────────────────────────────
chmod +x "$TMP"

INSTALL_DIR="/usr/local/bin"
DEST="${INSTALL_DIR}/deltapro"

echo "==> Installing to ${DEST}..."
if [ -w "$INSTALL_DIR" ]; then
  mv "$TMP" "$DEST"
else
  sudo mv "$TMP" "$DEST"
fi

echo ""
echo "==> deltapro installed successfully!"
echo "    Run: deltapro --version"