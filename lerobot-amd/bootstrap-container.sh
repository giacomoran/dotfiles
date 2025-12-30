#!/bin/bash
set -euo pipefail

# Setup script for LeRobot on AMD Developer Cloud
#
# Assumptions:
# - Running inside the rocm Docker container (docker exec -it rocm /bin/bash)
# - Image: rocm/pytorch:rocm7.0_ubuntu24.04_py3.12_pytorch_release_2.7.1
# - PyTorch 2.7.1 with ROCm 7.0 is pre-installed
#
# Based on AMD hackathon instructions for LeRobot v0.4.2

# Path to this setup's fish-config.fish in the GitHub repository
FISH_CONFIG_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-amd/fish-config.fish"

cd ~

# Install ffmpeg 7.x (required by LeRobot)
add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y

# Add eza repository (skip if already configured)
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | tee /etc/apt/sources.list.d/gierens.list > /dev/null
    chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

apt-get update
apt-get install -y \
    bat \
    direnv \
    dtach \
    eza \
    ffmpeg \
    fish \
    fzf \
    git-extras \
    htop \
    ripgrep \
    tree

# On Ubuntu, bat is installed as batcat, create symlink so 'bat' works
if command -v batcat &> /dev/null && ! command -v bat &> /dev/null; then
    ln -sf /usr/bin/batcat /usr/local/bin/bat
fi

# Install starship
if ! command -v starship &> /dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- -y
fi

# Install croc (file transfer tool)
if ! command -v croc &> /dev/null; then
    curl -sS https://getcroc.schollz.com | bash
fi

# Setup fish shell
chsh -s /usr/bin/fish
mkdir -p ~/.config/fish
curl -fsSL "$FISH_CONFIG_URL" | tee ~/.config/fish/config.fish > /dev/null

# Git config
git config --global user.name "Giacomo Randazzo"
EMAIL_USER="giacomoran"
EMAIL_DOMAIN="gmail.com"
git config --global user.email "${EMAIL_USER}@${EMAIL_DOMAIN}"

# Clone and install LeRobot
git clone https://github.com/huggingface/lerobot.git
cd lerobot
git checkout -b v0.4.2 v0.4.2
pip install -e .

echo ""
echo "LeRobot setup complete!"
echo ""
echo "Next steps:"
echo "  1. Login to Hugging Face: hf auth login"
echo "  2. Login to Weights & Biases: wandb login"
echo "  3. Start training (example):"
echo "     lerobot-train \\"
echo "       --dataset.repo_id=YOUR_HF_USER/YOUR_DATASET \\"
echo "       --policy.type=act \\"
echo "       --policy.device=cuda \\"
echo "       --output_dir=outputs/train/my_run \\"
echo "       --job_name=my_run"
echo ""
echo "Run 'fish' to start the fish shell (or reconnect to the container)"
