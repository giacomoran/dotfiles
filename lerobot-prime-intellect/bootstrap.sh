#!/bin/bash
set -euo pipefail

# Bootstrap script for LeRobot on Prime Intellect
#
# Create a Prime Intellect template with:
#   - Image: nvidia/cuda:12.4.1-devel-ubuntu22.04
#   - Startup script: paste this entire file
#   - Environment variables:
#       TAILSCALE_AUTH_KEY  - Tailscale auth key (https://login.tailscale.com/admin/settings/keys)
#       SSH_PUBLIC_KEY      - SSH public key (optional, has default)

TARGET_USER="giacomoran"
SSH_PUBLIC_KEY="${SSH_PUBLIC_KEY:-ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjL/ZlZCuKyJC345XIDkUo0/MDVvPB5McUXBjr57woa}"

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
apt-get install -y curl sudo software-properties-common

# Create user if doesn't exist
if ! id "$TARGET_USER" &>/dev/null; then
    echo "Creating user $TARGET_USER..."
    useradd -m -s /bin/bash "$TARGET_USER"
    usermod -aG sudo "$TARGET_USER"
    # Add to video/render groups only if they exist
    getent group video &>/dev/null && usermod -aG video "$TARGET_USER"
    getent group render &>/dev/null && usermod -aG render "$TARGET_USER"
    echo "$TARGET_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$TARGET_USER"
    chmod 0440 "/etc/sudoers.d/$TARGET_USER"
fi

# Setup SSH key
USER_HOME="/home/$TARGET_USER"
mkdir -p "$USER_HOME/.ssh"
echo "$SSH_PUBLIC_KEY" > "$USER_HOME/.ssh/authorized_keys"
chmod 700 "$USER_HOME/.ssh"
chmod 600 "$USER_HOME/.ssh/authorized_keys"
chown -R "$TARGET_USER:$TARGET_USER" "$USER_HOME/.ssh"

# Install and configure Tailscale
if [ -n "${TAILSCALE_AUTH_KEY:-}" ]; then
    echo "Setting up Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.d/99-tailscale.conf
    echo 'net.ipv6.conf.all.forwarding = 1' >> /etc/sysctl.d/99-tailscale.conf
    sysctl -p /etc/sysctl.d/99-tailscale.conf
    tailscale up --auth-key="$TAILSCALE_AUTH_KEY"
    tailscale set --ssh
else
    echo "TAILSCALE_AUTH_KEY not set, skipping Tailscale setup"
fi

echo ""
echo "=== System setup complete ==="
echo ""
echo "Next steps:"
echo "  1. SSH in: ssh $TARGET_USER@<tailscale-hostname>"
echo "  2. Run: curl -fsSL $BOOTSTRAP_USER_URL | bash"
echo ""
