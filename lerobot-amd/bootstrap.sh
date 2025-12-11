#!/bin/bash
set -euo pipefail

# Bootstrap script for AMD Developer Cloud LeRobot setup
#
# Assumptions:
# - cloud-init ran first (giacomoran user exists, SSH keys configured, Tailscale running)
# - Running as giacomoran user (via cloud-init)
# - Running on the host VM, not inside a Docker container
# - Ubuntu-based image
# - ROCm Docker container is already running (named 'rocm')

# Path to bootstrap-container.sh in the GitHub repository
BOOTSTRAP_CONTAINER_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-amd/bootstrap-container.sh"

# Install dtach on host
sudo apt-get update
sudo apt-get install -y dtach

# Run container bootstrap inside the Docker container
echo "Running container bootstrap..."
docker exec rocm bash -c "curl -fsSL $BOOTSTRAP_CONTAINER_URL | bash"

echo ""
echo "Setup complete!"
echo ""
echo "Connect to the container with:"
echo "  dtach -A /tmp/rocm docker exec -it rocm /usr/bin/fish"
echo ""
echo "Inside the container, use 'dev' to start a persistent dtach session."
