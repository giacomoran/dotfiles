#!/bin/bash
set -euo pipefail

# RunPod bootstrap script (run as root)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/bootstrap.sh | bash

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

USERNAME="giacomoran"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjL/ZlZCuKyJC345XIDkUo0/MDVvPB5McUXBjr57woa giacomoran@gmail.com"

echo "=== Creating user $USERNAME ==="

if ! id "$USERNAME" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo "$USERNAME"
    # Lock password (no password login)
    passwd -l "$USERNAME"
    mkdir -p /etc/sudoers.d
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
    chmod 440 /etc/sudoers.d/$USERNAME
fi

# Install only the public key for SSH access
mkdir -p /home/$USERNAME/.ssh
chmod 700 /home/$USERNAME/.ssh
echo "$PUBLIC_KEY" > /home/$USERNAME/.ssh/authorized_keys
chmod 600 /home/$USERNAME/.ssh/authorized_keys
chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh

echo "=== Hardening SSH ==="

# Disable root login and password authentication
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    # Restart SSH if systemd is available (may not be on RunPod containers)
    if command -v systemctl &>/dev/null && systemctl is-active sshd &>/dev/null; then
        systemctl restart sshd
    elif command -v service &>/dev/null; then
        service ssh restart 2>/dev/null || true
    fi
fi

echo "=== Installing system packages ==="

apt-get update

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

# Set fish as user's shell
chsh -s /usr/bin/fish "$USERNAME"

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
        aarch64) ZELLIJ_ARCH="aarch64-unknown-linux-musl" ;;
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

echo "=== Running user setup as $USERNAME ==="

su - $USERNAME -c "curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-user.sh | bash"

echo ""
echo "=========================================="
echo "Bootstrap complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Switch user: su - $USERNAME"
echo "  2. Start fish: exec fish"
echo "  3. For LeRobot: curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/lerobot-runpod/setup-lerobot.sh | bash"
echo ""
