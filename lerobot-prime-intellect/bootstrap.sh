#!/bin/bash
set -euo pipefail

# Bootstrap script for LeRobot on Prime Intellect
#
# Create a Prime Intellect template with:
#   - Image: nvidia/cuda:12.4.1-devel-ubuntu22.04
#   - Startup script: paste this entire file

TARGET_USER="giacomoran"
SSH_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjL/ZlZCuKyJC345XIDkUo0/MDVvPB5McUXBjr57woa"

# Path to bootstrap-user.sh in the GitHub repository
BOOTSTRAP_USER_URL="https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-prime-intellect/bootstrap-user.sh"

# =============================================================================
# Main
# =============================================================================

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

echo "=== Running as root, setting up system ==="

# Ensure basic tools are available
apt-get update
apt-get install -y curl sudo openssh-server

# Create user if doesn't exist
if ! id "$TARGET_USER" &>/dev/null; then
    echo "Creating user $TARGET_USER..."
    useradd -m -s /bin/bash "$TARGET_USER"
fi

# Always ensure sudo group and passwordless sudo (even if user exists)
usermod -aG sudo "$TARGET_USER"
# Add to video/render groups only if they exist
getent group video &>/dev/null && usermod -aG video "$TARGET_USER"
getent group render &>/dev/null && usermod -aG render "$TARGET_USER"

# Setup passwordless sudo
echo "$TARGET_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$TARGET_USER"
chmod 0440 "/etc/sudoers.d/$TARGET_USER"

# Setup SSH key
USER_HOME="/home/$TARGET_USER"
mkdir -p "$USER_HOME/.ssh"
echo "$SSH_PUBLIC_KEY" > "$USER_HOME/.ssh/authorized_keys"
chmod 700 "$USER_HOME/.ssh"
chmod 600 "$USER_HOME/.ssh/authorized_keys"
chown -R "$TARGET_USER:$TARGET_USER" "$USER_HOME/.ssh"

# Configure and start SSH server
mkdir -p /run/sshd
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

echo "Starting SSH server..."
/usr/sbin/sshd

echo ""
echo "=== System setup complete ==="
echo ""
echo "Next steps:"
echo "  1. SSH in: ssh $TARGET_USER@<public-ip>"
echo "  2. Run: curl -fsSL $BOOTSTRAP_USER_URL | bash"
echo ""
