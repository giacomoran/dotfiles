#!/bin/bash
set -euo pipefail

# LeRobot setup script (run after bootstrap.sh)
# Follows official installation: https://huggingface.co/docs/lerobot/installation
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-lerobot.sh | bash

cd ~

echo "=== Installing miniforge ==="

if [ ! -d "$HOME/miniforge3" ]; then
    curl -fsSL "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -o /tmp/miniforge.sh
    bash /tmp/miniforge.sh -b -p "$HOME/miniforge3"
    rm /tmp/miniforge.sh
fi

# Initialize conda for this session
eval "$("$HOME/miniforge3/bin/conda" shell.bash hook)"

echo "=== Creating lerobot conda environment ==="

if ! conda env list | grep -q "^lerobot "; then
    conda create -y -n lerobot python=3.11
fi

conda activate lerobot

echo "=== Installing ffmpeg ==="

conda install -y ffmpeg=7.1.1 -c conda-forge

echo "=== Installing PyTorch with CUDA ==="

pip install torch==2.7.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

echo "=== Cloning and installing LeRobot ==="

if [ ! -d ~/lerobot ]; then
    git clone https://github.com/huggingface/lerobot.git ~/lerobot
fi

cd ~/lerobot
git fetch --tags
git checkout v0.4.2 2>/dev/null || git checkout -b v0.4.2 v0.4.2

pip install -e .

echo "=== Initializing conda for fish shell ==="

# Only run conda init if not already configured (idempotent)
if ! grep -q "conda initialize" ~/.config/fish/config.fish 2>/dev/null; then
    conda init fish
fi

echo ""
echo "=========================================="
echo "LeRobot setup complete!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  conda activate lerobot"
echo ""
echo "Next steps:"
echo "  1. Restart shell or run: exec fish"
echo "  2. Activate env: conda activate lerobot"
echo "  3. Verify GPU: python -c \"import torch; print(f'torch={torch.__version__}, cuda={torch.version.cuda}, available={torch.cuda.is_available()}')\""
echo "  4. Login to Hugging Face: hf auth login"
echo "  5. Login to Weights & Biases: wandb login"
echo ""
