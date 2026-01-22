#!/bin/bash
set -euo pipefail

# User setup script for LeRobot on Prime Intellect
#
# This script is called by bootstrap.sh after user creation.
# It runs as the target user (giacomoran), not root.

FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-prime-intellect/config/fish/fish-config.fish"
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-prime-intellect/config/zellij/config.kdl"

cd ~

echo "=== Installing system packages ==="

# Add ffmpeg 7.x PPA (required by LeRobot)
sudo add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y

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
    ffmpeg \
    fish \
    fzf \
    git \
    git-extras \
    htop \
    ripgrep \
    tree

# On Ubuntu, bat is installed as batcat
if command -v batcat &> /dev/null && ! command -v bat &> /dev/null; then
    sudo ln -sf /usr/bin/batcat /usr/local/bin/bat
fi

echo "=== Installing CLI tools ==="

# Install starship prompt
if ! command -v starship &> /dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- -y
fi

# Install croc (file transfer tool)
if ! command -v croc &> /dev/null; then
    curl -sS https://getcroc.schollz.com | bash
fi

# Install zellij (terminal multiplexer)
if ! command -v zellij &> /dev/null; then
    ARCH=$(uname -m)
    case "$ARCH" in
        aarch64) ZELLIJ_ARCH="aarch64-unknown-linux-gnu" ;;
        x86_64)  ZELLIJ_ARCH="x86_64-unknown-linux-musl" ;;
        *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    cd /tmp
    curl -fsSL "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ZELLIJ_ARCH}.tar.gz" | tar -xvz
    sudo mv zellij /usr/local/bin/
    cd ~
fi

# Install micro editor
if ! command -v micro &> /dev/null; then
    cd /tmp
    curl -fsSL https://getmic.ro | bash
    sudo mv micro /usr/local/bin/
    cd ~
fi

# Install uv (fast Python package manager)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Add uv to PATH for this session
export PATH="$HOME/.local/bin:$PATH"

echo "=== Setting up shell configuration ==="

# Setup fish shell
sudo chsh -s /usr/bin/fish "$(whoami)"
mkdir -p ~/.config/fish
curl -fsSL "$FISH_CONFIG_URL" -o ~/.config/fish/config.fish

# Setup zellij config
mkdir -p ~/.config/zellij
curl -fsSL "$ZELLIJ_CONFIG_URL" -o ~/.config/zellij/config.kdl

# Git config
git config --global user.name "Giacomo Randazzo"
git config --global user.email "giacomoran@gmail.com"

echo "=== Setting up Python environment ==="

cd ~
uv venv --python 3.10 .venv

# Install PyTorch 2.7.1 with CUDA 12.4 support
uv pip install --python .venv/bin/python \
    torch==2.7.1 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

echo "=== Cloning and installing LeRobot ==="

# Clone LeRobot (skip if already exists)
if [ ! -d ~/lerobot ]; then
    git clone https://github.com/huggingface/lerobot.git ~/lerobot
fi

cd ~/lerobot
git fetch --tags
git checkout v0.4.2 2>/dev/null || git checkout -b v0.4.2 v0.4.2

# Install LeRobot
uv pip install --python ~/.venv/bin/python -e .

cd ~

echo ""
echo "=========================================="
echo "LeRobot setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. SSH in via Tailscale"
echo "  2. Fish + zellij auto-start, venv auto-activates"
echo "  3. Verify GPU: python -c \"import torch; print(torch.cuda.is_available())\""
echo "  4. Login to Hugging Face: huggingface-cli login"
echo "  5. Login to Weights & Biases: wandb login"
echo ""
