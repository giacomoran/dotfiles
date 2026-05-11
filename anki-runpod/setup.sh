#!/bin/bash
set -euo pipefail

# RunPod setup - run as your user (not root)
#
# Prerequisites: bootstrap.sh has run (you have sudo access)
#
# Usage (as giacomoran):
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/setup.sh | bash

if [ "$(id -u)" -eq 0 ]; then
    echo "Error: Don't run this as root. Run as your user (you have sudo)."
    exit 1
fi

FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/config/fish/fish-config.fish"
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/config/zellij/config.kdl"

echo "=== Installing system packages ==="

# Add eza repository
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | sudo gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | sudo tee /etc/apt/sources.list.d/gierens.list > /dev/null
    sudo chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

sudo apt-get update
sudo apt-get install -y \
    bat \
    direnv \
    eza \
    fish \
    fzf \
    git \
    git-extras \
    htop \
    nvtop \
    ripgrep \
    rsync \
    tree

# On Ubuntu, bat is installed as batcat
if command -v batcat &> /dev/null && ! command -v bat &> /dev/null; then
    sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
fi

echo "=== Installing CLI tools ==="

# Install starship prompt
if ! command -v starship &> /dev/null; then
    curl -sS https://starship.rs/install.sh | sudo sh -s -- -y
fi

# Install croc (file transfer tool)
if ! command -v croc &> /dev/null; then
    curl -sS https://getcroc.schollz.com | sudo bash
fi

# Install zellij (terminal multiplexer)
if ! command -v zellij &> /dev/null; then
    ARCH=$(uname -m)
    case "$ARCH" in
        aarch64) ZELLIJ_ARCH="aarch64-unknown-linux-musl" ;;
        x86_64)  ZELLIJ_ARCH="x86_64-unknown-linux-musl" ;;
        *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    curl -fsSL "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ZELLIJ_ARCH}.tar.gz" -o /tmp/zellij.tar.gz
    sudo tar -xzf /tmp/zellij.tar.gz -C /usr/local/bin
    rm /tmp/zellij.tar.gz
fi

# Install micro editor
if ! command -v micro &> /dev/null; then
    curl https://getmic.ro | sudo bash
    sudo mv micro /usr/local/bin/ 2>/dev/null || true
fi

# Install uv (Python package manager)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "=== Setting up shell ==="

# Set fish as default shell
sudo chsh -s /usr/bin/fish "$USER"

# Fish config
mkdir -p ~/.config/fish
curl -fsSL "$FISH_CONFIG_URL" -o ~/.config/fish/config.fish

# Zellij config
mkdir -p ~/.config/zellij
curl -fsSL "$ZELLIJ_CONFIG_URL" -o ~/.config/zellij/config.kdl

# Git config
git config --global user.name "Giacomo Randazzo"
git config --global user.email "giacomoran@gmail.com"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Start a new shell (fish) or run: exec fish"
echo ""
echo "To set up the workspace (repo + uv deps):"
echo "  curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/setup-workspace.sh | bash"
echo ""
