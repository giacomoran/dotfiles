#!/bin/bash
set -euo pipefail

# Bootstrap script for LeRobot on RunPod
#
# Usage:
#   1. Create a RunPod pod with template: runpod/pytorch:2.4.0-py3.10-cuda12.4.1-devel-ubuntu22.04
#   2. Add your SSH key via RunPod UI
#   3. Set startup command: curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/bootstrap.sh | bash
#   4. Or SSH in and run the curl command manually

FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/fish/fish-config.fish"
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/zellij/config.kdl"

cd ~

echo "=== Installing system packages ==="

# Add ffmpeg 7.x PPA (required by LeRobot)
add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y

# Add eza repository
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | tee /etc/apt/sources.list.d/gierens.list > /dev/null
    chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

apt-get update
apt-get install -y \
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
    ln -sf /usr/bin/batcat /usr/local/bin/bat
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
    mv zellij /usr/local/bin/
    cd ~
fi

# Install micro editor
if ! command -v micro &> /dev/null; then
    cd /tmp
    curl -fsSL https://getmic.ro | bash
    mv micro /usr/local/bin/
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
chsh -s /usr/bin/fish
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

# Install PyTorch with CUDA 12.4 support
uv pip install --python .venv/bin/python \
    torch \
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
echo "  1. Start fish: exec fish"
echo "  2. Verify GPU: python -c \"import torch; print(torch.cuda.is_available())\""
echo "  3. Login to Hugging Face: huggingface-cli login"
echo "  4. Login to Weights & Biases: wandb login"
echo ""
