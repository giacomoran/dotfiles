#!/bin/bash
set -euo pipefail

# User bootstrap for epsilon
#
# Assumptions:
# - bootstrap-root.sh ran first (packages, fish login shell, lingering, tailscale operator)
# - Running as giacomoran, from a copy of this folder on epsilon, so config files sit next to it:
#     ssh giacomoran@epsilon 'mkdir -p ~/.dotfiles-remote/epsilon'
#     rsync -a --delete epsilon/ giacomoran@epsilon:~/.dotfiles-remote/epsilon/
#     ssh giacomoran@epsilon 'bash ~/.dotfiles-remote/epsilon/bootstrap.sh'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Node version for global tools (T3 Code needs 22.16+). Projects pin their own versions.
NODE_VERSION="24"

# Install fish config
mkdir -p ~/.config/fish
cp "$SCRIPT_DIR/config/fish/fish-config.fish" ~/.config/fish/config.fish

# Install zellij config
mkdir -p ~/.config/zellij
cp "$SCRIPT_DIR/config/zellij/config.kdl" ~/.config/zellij/config.kdl

# Git config
git config --global user.name "Giacomo Randazzo"
EMAIL_USER="giacomoran"
EMAIL_DOMAIN="gmail.com"
git config --global user.email "${EMAIL_USER}@${EMAIL_DOMAIN}"
git config --global init.defaultBranch main

# Projects live in ~/Projects, as on the Mac
mkdir -p ~/Projects

# Give systemd user services (T3 Code and the agents it spawns) the same tool PATH as fish.
# The 999- prefix sorts after Ubuntu's 99-environment.conf, which resets PATH from /etc/environment.
mkdir -p ~/.config/environment.d
rm -f ~/.config/environment.d/10-path.conf
cat > ~/.config/environment.d/999-path.conf <<'EOF'
PATH=${HOME}/.local/share/mise/shims:${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}
EOF

# Let Vite-based dev servers started with --host answer at http://epsilon:<port>. Vite
# rejects host names it doesn't know; this adds epsilon's tailnet names for every project
# without touching their configs. The firewall keeps those servers tailnet-only.
cat > ~/.config/environment.d/999-dev-servers.conf <<'EOF'
__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS=epsilon,epsilon.tail52f04e.ts.net
EOF

# Make MuJoCo render through EGL, since there is no display (ai-saldatura's cameras)
cat > ~/.config/environment.d/999-mujoco.conf <<'EOF'
MUJOCO_GL=egl
EOF

# Make glibc hand freed memory back to the system. By default a long-lived process keeps its
# peak, so ai-saldatura's 16 pytest workers each grew to 8-9 GB and earlyoom killed them.
cat > ~/.config/environment.d/999-malloc.conf <<'EOF'
MALLOC_ARENA_MAX=2
MALLOC_TRIM_THRESHOLD_=65536
EOF

# Install uv (Python versions and environments)
if [ ! -x ~/.local/bin/uv ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install mise (Node versions; reads the same .tool-versions files as asdf on the Mac)
if [ ! -x ~/.local/bin/mise ]; then
    curl -fsSL https://mise.run | sh
fi
~/.local/bin/mise use --global "node@$NODE_VERSION"

# Install pnpm as its own mise tool, so it works with whatever Node version a project pins
# (corepack's pnpm only exists in the Node install where it was enabled). pnpm switches itself
# to the version in a project's packageManager field.
~/.local/bin/mise exec -- corepack disable pnpm
~/.local/bin/mise use --global pnpm@10

# Install Claude Code
if [ ! -x ~/.local/bin/claude ]; then
    curl -fsSL https://claude.ai/install.sh | bash
fi

# Install Codex
~/.local/bin/mise exec -- npm install --global @openai/codex
~/.local/bin/mise reshim

# Install the instructions Claude Code and Codex follow in every project
mkdir -p ~/.claude ~/.codex
cp "$SCRIPT_DIR/config/agents/CLAUDE.md" ~/.claude/CLAUDE.md
cp "$SCRIPT_DIR/config/agents/AGENTS.md" ~/.codex/AGENTS.md

# Install Obsidian Headless, which syncs the vault through Obsidian Sync without the app.
# Its SQLite dependency needs its install script, which npm blocks by default.
~/.local/bin/mise exec -- npm install --global --allow-scripts=better-sqlite3 obsidian-headless
~/.local/bin/mise reshim
# The service needs a login first (see README.md), so it is only installed here, not enabled
mkdir -p ~/.config/systemd/user ~/Obsidian/giacomo
cp "$SCRIPT_DIR/config/systemd/obsidian-sync.service" ~/.config/systemd/user/
systemctl --user daemon-reload

# Install relay-cli (rmd), which syncs the vault's Relay shared folders without the app. Pinned,
# since it is young and runs Relay's sync engine on files agents edit. Its service needs a
# login and clones first (see README.md), so it is only installed here, not enabled
RMD_REVISION=1c6d6cb210e7e1d60ac59e43ad7a28b4e27cb73b
if [ "$(cat ~/.local/share/relay-cli/current/revision 2>/dev/null)" != "$RMD_REVISION" ]; then
    curl -fsSL "https://raw.githubusercontent.com/No-Instructions/relay-cli/$RMD_REVISION/install.sh" | RMD_REVISION="$RMD_REVISION" bash
fi
cp "$SCRIPT_DIR/config/systemd/relay.service" ~/.config/systemd/user/
systemctl --user daemon-reload

# Install qmd, the vault's search engine, with the same collections as on the Mac.
# Its SQLite and llama.cpp dependencies need their install scripts.
~/.local/bin/mise exec -- npm install --global --allow-scripts=better-sqlite3,node-llama-cpp @tobilu/qmd@2.8.3
~/.local/bin/mise reshim
mkdir -p ~/.config/qmd ~/.local/share/qmd-pdf ~/.cache/qmd-pdf/sources-docs
cp "$SCRIPT_DIR/config/qmd/index.yml" ~/.config/qmd/index.yml
# PDF-to-markdown converter for the sources-docs collection (text layer only, no OCR)
cp "$SCRIPT_DIR/config/qmd/pdf_to_markdown.py" ~/.local/share/qmd-pdf/pdf_to_markdown.py
if [ ! -x ~/.local/share/qmd-pdf/.venv/bin/python ]; then
    ~/.local/bin/uv venv ~/.local/share/qmd-pdf/.venv
fi
~/.local/bin/uv pip install --python ~/.local/share/qmd-pdf/.venv/bin/python pymupdf
# Re-index every 15 minutes, so notes edited on the Mac show up in searches. Enabled
# after the first index, see README.md
cp "$SCRIPT_DIR/config/qmd/qmd-update.service" "$SCRIPT_DIR/config/qmd/qmd-update.timer" ~/.config/systemd/user/
systemctl --user daemon-reload

# Install T3 Code and run it as a user service that starts at boot
if [ ! -x ~/.local/bin/t3 ]; then
    curl -fsSL https://t3.codes/install.sh | sh
fi
~/.local/bin/t3 service install
