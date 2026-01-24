#!/bin/bash
set -euo pipefail

# Bootstrap script for LeRobot on RunPod
#
# Usage:
#   1. Create a RunPod pod with template: runpod/pytorch:2.4.0-py3.10-cuda12.4.1-devel-ubuntu22.04
#   2. Add your SSH key via RunPod UI
#   3. Set startup command: curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/bootstrap.sh | bash
#   4. Or SSH in and run the curl command manually

USERNAME="giacomoran"
PASSWORD="magia"
FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/fish/fish-config.fish"
ZELLIJ_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/config/zellij/config.kdl"

# =============================================================================
# Phase 1: Root setup (system packages, user creation)
# =============================================================================

if [ "$(id -u)" -eq 0 ]; then
    echo "=== Creating user $USERNAME ==="

    if ! id "$USERNAME" &>/dev/null; then
        useradd -m -s /usr/bin/fish -G sudo "$USERNAME"
        echo "$USERNAME:$PASSWORD" | chpasswd
        # Allow sudo without password for convenience on ephemeral VMs
        echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
    fi

    # Copy SSH keys from root to new user
    if [ -d /root/.ssh ]; then
        cp -r /root/.ssh /home/$USERNAME/.ssh
        chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh
    fi

    echo "=== Installing system packages ==="

    apt-get update

    # Add ffmpeg 7.x PPA manually (avoid add-apt-repository which breaks on RunPod containers)
    if [ ! -f /etc/apt/sources.list.d/ffmpeg7.list ]; then
        echo "deb https://ppa.launchpadcontent.net/ubuntuhandbook1/ffmpeg7/ubuntu jammy main" | tee /etc/apt/sources.list.d/ffmpeg7.list
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A088A0E4B5E5EF30B85DC56402D87F1082C54377
    fi

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
        curl -fsSL "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ZELLIJ_ARCH}.tar.gz" -o /tmp/zellij.tar.gz
        tar -xzf /tmp/zellij.tar.gz -C /usr/local/bin
        rm /tmp/zellij.tar.gz
    fi

    # Install micro editor
    if ! command -v micro &> /dev/null; then
        curl -fsSL https://getmic.ro | bash
        mv micro /usr/local/bin/
    fi

    echo "=== Switching to user $USERNAME for user setup ==="

    # Download this script and run phase 2 as the new user
    SCRIPT_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/bootstrap.sh"
    sudo -u "$USERNAME" bash -c "curl -fsSL '$SCRIPT_URL' | bash"

    echo ""
    echo "=========================================="
    echo "Bootstrap complete!"
    echo "=========================================="
    echo ""
    echo "Switch to user: su - $USERNAME"
    echo ""
    exit 0
fi

# =============================================================================
# Phase 2: User setup (runs as $USERNAME)
# =============================================================================

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

echo "=== Setting up Python environment ==="

uv venv --python 3.10 ~/.venv

uv pip install --python ~/.venv/bin/python \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu124

echo "=== Cloning and installing LeRobot ==="

if [ ! -d ~/lerobot ]; then
    git clone https://github.com/huggingface/lerobot.git ~/lerobot
fi

cd ~/lerobot
git fetch --tags
git checkout v0.4.2 2>/dev/null || git checkout -b v0.4.2 v0.4.2

uv pip install --python ~/.venv/bin/python -e .

cd ~

echo ""
echo "=========================================="
echo "User setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify GPU: python -c \"import torch; print(torch.cuda.is_available())\""
echo "  2. Login to Hugging Face: huggingface-cli login"
echo "  3. Login to Weights & Biases: wandb login"
echo ""
