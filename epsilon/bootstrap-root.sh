#!/bin/bash
set -euo pipefail

# Root bootstrap for epsilon
#
# epsilon is an always-on home server (Trigkey S5, Ryzen 7 5800H, 32 GB) that runs
# T3 Code and coding agents. See README.md for the full setup order.
#
# Assumptions:
# - Ubuntu Server 26.04 installed with the giacomoran user (sudo needs a password)
# - Tailscale up with `tailscale up --ssh`, so root is reachable over Tailscale SSH
# - Run as root from the Mac:
#     ssh root@epsilon 'bash -s' < epsilon/bootstrap-root.sh

USERNAME="giacomoran"

# Use the local timezone, so logs and cron-like timers match wall-clock time at home
timedatectl set-timezone Europe/Rome

# Add eza repository (skip if already configured)
if [ ! -f /etc/apt/keyrings/gierens.gpg ]; then
    mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" > /etc/apt/sources.list.d/gierens.list
    chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
fi

# Add GitHub CLI repository (skip if already configured)
if [ ! -f /etc/apt/keyrings/githubcli-archive-keyring.gpg ]; then
    mkdir -p -m 755 /etc/apt/keyrings
    wget -qO /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
fi

# Install base packages, plus hardware monitoring and OOM protection for a 24/7 box
apt-get update
apt-get install -y \
    bat \
    build-essential \
    curl \
    direnv \
    earlyoom \
    eza \
    fish \
    fzf \
    gh \
    git \
    git-extras \
    gnupg \
    htop \
    jq \
    less \
    lm-sensors \
    nvme-cli \
    ripgrep \
    smartmontools \
    tree \
    unzip \
    wget

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

# Install zellij (terminal multiplexer)
if ! command -v zellij &> /dev/null; then
    curl -fsSL "https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz" | tar -xz -C /usr/local/bin zellij
fi

# Install micro editor
if ! command -v micro &> /dev/null; then
    (cd /usr/local/bin && curl https://getmic.ro | bash)
fi

# Use fish as the login shell
chsh -s /usr/bin/fish "$USERNAME"

# Let user services (T3 Code) start at boot and keep running without a login session
loginctl enable-linger "$USERNAME"

# Let giacomoran manage `tailscale serve` without sudo, which `t3 pair --tailscale` needs
tailscale set --operator="$USERNAME"

# Use the AMD hardware watchdog: systemd pings it, and if the kernel hangs the board resets.
# Ubuntu blacklists the driver, and both systemd-modules-load and the initramfs honor the blacklist,
# while a plain `modprobe sp5100_tco` doesn't. systemd only looks for a watchdog early in boot, so
# a service loads the driver later and then sets the timeout over D-Bus, which makes systemd open it.
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/watchdog.conf <<'EOF'
[Manager]
RuntimeWatchdogSec=30s
RebootWatchdogSec=2min
EOF
cat > /etc/systemd/system/watchdog-sp5100.service <<'EOF'
[Unit]
Description=Load the AMD SP5100 hardware watchdog and hand it to systemd
After=dbus.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/modprobe sp5100_tco
ExecStart=/usr/bin/busctl set-property org.freedesktop.systemd1 /org/freedesktop/systemd1 org.freedesktop.systemd1.Manager RuntimeWatchdogUSec t 30000000

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now watchdog-sp5100.service

# Kill the biggest memory hog before the box freezes, but never the processes we need to reach it.
# No quotes around the regex: systemd splits $EARLYOOM_ARGS on whitespace and keeps quotes literally.
cat > /etc/default/earlyoom <<'EOF'
EARLYOOM_ARGS="-r 3600 --avoid (^|/)(init|systemd|sshd|tailscaled|t3)$"
EOF
systemctl enable --now earlyoom
systemctl restart earlyoom

# Make hard-coded macOS paths (CLAUDE.md files, skills, scripts) resolve on Linux
mkdir -p /Users
ln -sfn "/home/$USERNAME" "/Users/$USERNAME"
