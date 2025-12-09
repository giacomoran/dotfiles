#!/bin/bash
set -euo pipefail

# Bootstrap script for general remote setup
#
# Assumptions:
# - cloud-init ran first (giacomo user exists, SSH keys configured, Tailscale running)
# - Running on a VM, not inside a Docker container
# - Ubuntu-based image

# WARN: Update when copying this file in a different setup
# Path to this setup's fish-config.fish in the GitHub repository
FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/general/fish-config.fish"

# Detect if running as root or need sudo
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
fi

# Add eza repository (skip if already configured)
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    $SUDO mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | $SUDO gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | $SUDO tee /etc/apt/sources.list.d/gierens.list > /dev/null
    $SUDO chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

$SUDO apt-get update
$SUDO apt-get install -y \
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
    $SUDO ln -sf /usr/bin/batcat /usr/local/bin/bat
fi

# Install starship
if ! command -v starship &> /dev/null; then
    curl -sS https://starship.rs/install.sh | $SUDO sh -s -- -y
fi

# Install fish shell
$SUDO chsh -s /usr/bin/fish giacomo
$SUDO -u giacomo mkdir -p /home/giacomo/.config/fish
curl -fsSL "$FISH_CONFIG_URL" | $SUDO -u giacomo tee /home/giacomo/.config/fish/config.fish > /dev/null

# Git config
$SUDO -u giacomo sh -c 'git config --global user.name "Giacomo Randazzo" && git config --global user.email "giacomoran@gmail.com"'
