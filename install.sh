#!/usr/bin/env bash
set -euo pipefail

# Sprite Forge installer
# Usage: curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash

REPO="https://github.com/gididaf/sprite-forge.git"
INSTALL_DIR="$HOME/.sprite-forge"
BIN_DIR="$HOME/.local/bin"
SKILL_DIR="$HOME/.claude/skills"

echo "=== Sprite Forge Installer ==="

# ── Clone or update repo ──────────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    echo "[update] Pulling latest..."
    git -C "$INSTALL_DIR" pull --quiet
else
    echo "[install] Cloning sprite-forge..."
    git clone --quiet "$REPO" "$INSTALL_DIR"
fi

# ── Install Python dependency ─────────────────────────────────────────────
echo "[deps] Checking Pillow..."
python3 -c "import PIL" 2>/dev/null || {
    echo "[deps] Installing Pillow..."
    pip3 install --quiet Pillow
}

# ── Install rsvg-convert ──────────────────────────────────────────────────
if ! command -v rsvg-convert &>/dev/null; then
    echo "[deps] Installing librsvg..."
    if command -v brew &>/dev/null; then
        brew install --quiet librsvg
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y -qq librsvg2-bin
    else
        echo "[error] Cannot install librsvg. Install manually: brew install librsvg (macOS) or apt install librsvg2-bin (Linux)"
        exit 1
    fi
else
    echo "[deps] rsvg-convert: OK"
fi

# ── Symlink CLI tool ─────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/sprite-forge.py" "$BIN_DIR/sprite-forge"
chmod +x "$INSTALL_DIR/sprite-forge.py"
echo "[bin] Linked: sprite-forge -> $BIN_DIR/sprite-forge"

# ── Install Claude Code skill ────────────────────────────────────────────
mkdir -p "$SKILL_DIR/sprite-forge"
ln -sf "$INSTALL_DIR/.claude/skills/sprite-forge/SKILL.md" "$SKILL_DIR/sprite-forge/SKILL.md"
echo "[skill] Linked: /sprite-forge skill -> $SKILL_DIR/sprite-forge/SKILL.md"

# ── Check PATH ────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "[note] Add $BIN_DIR to your PATH:"
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
    echo ""
fi

echo ""
echo "=== Done! ==="
echo ""
echo "Usage in Claude Code (restart Claude Code first):"
echo "  /sprite-forge skeleton warrior walking left"
echo "  /sprite-forge make it red, modify hero.svg"
echo "  /sprite-forge add shield, based on hero.svg"
echo ""
echo "Standalone conversion:"
echo "  sprite-forge hero_walk_left.svg"
echo ""
