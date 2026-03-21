#!/bin/bash
# Amnezia VPN CLI — One-time installer
# Installs 'amnezia' as a global command on this machine
# Usage: bash install.sh

TOKEN="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"
REPO="sky-night-net/amnezia-deploy-tool"
SCRIPT_URL="https://raw.githubusercontent.com/${REPO}/main/amnezia-cli.py"
INSTALL_DIR="$HOME/.local/bin"
INSTALL_PATH="$INSTALL_DIR/amnezia"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Amnezia VPN CLI — Installer            ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Create bin dir if needed
mkdir -p "$INSTALL_DIR"

# Download script
echo "  [→] Downloading latest amnezia-cli.py..."
curl -fsSL \
  -H "Authorization: token ${TOKEN}" \
  "${SCRIPT_URL}" -o "${INSTALL_PATH}"

if [ $? -ne 0 ]; then
  echo "  [✘] Download failed. Check your internet connection."
  exit 1
fi

chmod +x "${INSTALL_PATH}"

# Add to PATH if needed
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
  SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
  if ! grep -q "$INSTALL_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
    echo "  [✔] Added $INSTALL_DIR to PATH in $SHELL_RC"
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

echo ""
echo "  [✔] Installed! Run from anywhere:"
echo ""
echo "      amnezia"
echo ""
echo "  To update to latest version anytime:"
echo ""
echo "      bash <(curl -fsSL https://${TOKEN}@raw.githubusercontent.com/${REPO}/main/install.sh)"
echo ""
