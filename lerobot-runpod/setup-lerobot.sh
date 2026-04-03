#!/bin/bash
set -euo pipefail

# LeRobot setup script (run after setup.sh)
# Follows official installation: https://huggingface.co/docs/lerobot/installation
#
# Uses a clean uv venv (no --system-site-packages) so that uv can resolve
# torch + torchcodec together. Inheriting the RunPod container's pre-installed
# PyTorch caused ABI mismatches with torchcodec (undefined C++ symbols).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-lerobot.sh | bash

cd ~

echo "=== Installing ffmpeg ==="

# Add ffmpeg 7.x PPA (Ubuntu 24.04 ships 6.x by default)
sudo add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y
sudo apt-get update
sudo apt-get install -y ffmpeg

echo "=== Creating Python venv ==="

# Clean venv — no --system-site-packages. Letting uv resolve torch + torchcodec
# together avoids ABI mismatches between the RunPod PyTorch build and torchcodec.
uv venv --python 3.12 ~/.venv

echo "=== Cloning and installing LeRobot ==="

if [ ! -d ~/lerobot ]; then
    git clone https://github.com/huggingface/lerobot.git ~/lerobot
fi

cd ~/lerobot
git fetch --tags
git checkout v0.5.0 2>/dev/null || git checkout -b v0.5.0 v0.5.0

# Install torch + torchvision first so uv can pick ABI-compatible torchcodec
uv pip install --python ~/.venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/.venv/bin/python -e .

echo "=== Installing lerobot-policy-act-smooth ==="

# Custom ACT-smooth policy — not on PyPI, install directly from GitHub
uv pip install --python ~/.venv/bin/python git+https://github.com/giacomoran/lerobot-policy-act-smooth.git

echo ""
echo "=========================================="
echo "LeRobot setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart shell or run: exec fish"
echo "  2. Venv auto-activates via direnv (cd into any project dir)"
echo "  3. Verify GPU: python -c \"import torch; print(f'torch={torch.__version__}, cuda={torch.version.cuda}, available={torch.cuda.is_available()}')\""
echo "  4. Login to Hugging Face: hf auth login"
echo "  5. Login to Weights & Biases: wandb login"
echo ""
