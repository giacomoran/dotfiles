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

cd ~

# Install ffmpeg 7.x (required by LeRobot)
add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y
apt update && apt install ffmpeg -y

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
