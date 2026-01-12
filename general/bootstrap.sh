#!/bin/bash
set -euo pipefail

# Bootstrap script for general remote setup
#
# Assumptions:
# - cloud-init ran first (giacomoran user exists, SSH keys configured, Tailscale running)
# - Running as giacomoran user (via cloud-init)
# - Running on a VM, not inside a Docker container
# - Ubuntu-based image

# WARN: Update when copying this file in a different setup
# Path to this setup's fish-config.fish in the GitHub repository
FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/general/config/fish/fish-config.fish"

# Add eza repository (skip if already configured)
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    sudo mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | sudo gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | sudo tee /etc/apt/sources.list.d/gierens.list > /dev/null
    sudo chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

sudo apt-get update
sudo apt-get install -y \
    bat \
    build-essential \
    curl \
    direnv \
    dtach \
    eza \
    fish \
    fzf \
    git \
    git-extras \
    gnupg \
    htop \
    less \
    ripgrep \
    tree \
    wget

# On Ubuntu, bat is installed as batcat, create symlink so 'bat' works
if command -v batcat &> /dev/null && ! command -v bat &> /dev/null; then
    sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
fi

# Install starship
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
    if [ "$ARCH" = "aarch64" ]; then
        ZELLIJ_ARCH="aarch64-unknown-linux-gnu"
    elif [ "$ARCH" = "x86_64" ]; then
        ZELLIJ_ARCH="x86_64-unknown-linux-musl"
    fi
    curl -fsSL https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ZELLIJ_ARCH}.tar.gz | tar -xvz && sudo mv zellij /usr/local/bin/
fi

# Install micro editor
if ! command -v micro &> /dev/null; then
    curl https://getmic.ro | sudo bash
fi

# Install fish shell
sudo chsh -s /usr/bin/fish giacomoran
mkdir -p ~/.config/fish
curl -fsSL "$FISH_CONFIG_URL" | tee ~/.config/fish/config.fish > /dev/null

# Setup zellij config
mkdir -p ~/.config/zellij
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/general/config/zellij/config.kdl"
curl -fsSL "$ZELLIJ_CONFIG_URL" | tee ~/.config/zellij/config.kdl > /dev/null

# Git config
git config --global user.name "Giacomo Randazzo"
EMAIL_USER="giacomoran"
EMAIL_DOMAIN="gmail.com"
git config --global user.email "${EMAIL_USER}@${EMAIL_DOMAIN}"
