#!/bin/bash
set -euo pipefail

# RunPod bootstrap - MINIMAL root setup
#
# ==========================================
# POD CREATION CHECKLIST
# ==========================================
#
# 1. Template (choose one):
#    - GPU:  RunPod PyTorch  (e.g. runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04)
#    - CPU:  RunPod PyTorch  (same image works; torch falls back to CPU automatically)
#
# 2. Network volume:
#    - Attach the `anki` volume (200 GB) mounted at /workspace
#
# 3. Container disk: 20 GB  (OS + tools; training outputs go to /workspace)
#
# 4. Expose ports:
#    - 43800 (HTTP)  →  Aim experiment tracker UI
#      Access at: https://<pod-id>-43800.proxy.runpod.net
#      Start with: uv run aim up --host 0.0.0.0
#
# ==========================================
# SETUP (once the pod is running)
# ==========================================
#
# This script ONLY creates your user account with sudo access.
# Run as root, then SSH as your user and run setup.sh.
#
# Usage (as root):
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/bootstrap.sh | bash

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

USERNAME="giacomoran"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjL/ZlZCuKyJC345XIDkUo0/MDVvPB5McUXBjr57woa giacomoran@gmail.com"

echo "=== Creating user $USERNAME with sudo access ==="

# Install sudo first (might not be present in container)
apt-get update
apt-get install -y sudo

# Create user if doesn't exist
if ! id "$USERNAME" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo "$USERNAME"
    passwd -l "$USERNAME"  # Lock password (SSH key only)
fi

# Setup passwordless sudo
mkdir -p /etc/sudoers.d
echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
chmod 440 /etc/sudoers.d/$USERNAME

# Setup SSH key
mkdir -p /home/$USERNAME/.ssh
chmod 700 /home/$USERNAME/.ssh
echo "$PUBLIC_KEY" > /home/$USERNAME/.ssh/authorized_keys
chmod 600 /home/$USERNAME/.ssh/authorized_keys
chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh

echo ""
echo "=========================================="
echo "Done! Now:"
echo "=========================================="
echo ""
echo "  1. SSH as $USERNAME (not root)"
echo "  2. Run: curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/setup.sh | bash"
echo ""
