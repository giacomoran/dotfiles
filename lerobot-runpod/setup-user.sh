#!/bin/bash
set -euo pipefail

# User setup script (run as user, after bootstrap.sh)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-user.sh | bash

FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/fish/fish-config.fish"
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/zellij/config.kdl"

cd ~

echo "=== Installing uv ==="

if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$PATH"

echo "=== Setting up shell configuration ==="

mkdir -p ~/.config/fish
curl -fsSL "$FISH_CONFIG_URL" -o ~/.config/fish/config.fish

mkdir -p ~/.config/zellij
curl -fsSL "$ZELLIJ_CONFIG_URL" -o ~/.config/zellij/config.kdl

git config --global user.name "Giacomo Randazzo"
git config --global user.email "giacomoran@gmail.com"

echo ""
echo "=========================================="
echo "User setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start fish: exec fish"
echo "  2. For LeRobot: curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-lerobot.sh | bash"
echo ""
