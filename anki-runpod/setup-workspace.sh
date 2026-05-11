#!/bin/bash
set -euo pipefail

# RunPod workspace setup - idempotent, run on each new pod
#
# - Clones ankihub-research into /workspace if not already there
# - Runs uv sync for code-py
#
# The network volume is mounted at /workspace. The repo and venv
# live there so they persist across pods. Run `git pull` to get
# fresh code on an existing clone.
#
# Usage (as giacomoran):
#   curl -fsSL https://raw.githubusercontent.com/giacomoran/dotfiles/remote/anki-runpod/setup-workspace.sh | bash

WORKSPACE="/workspace"
REPO_DIR="$WORKSPACE/ankihub-research"
REPO_URL="https://github.com/andrewsanchez/ankihub-research"

echo "=== Setting up workspace at $WORKSPACE ==="

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Cloning repo..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "Repo already cloned, pulling latest..."
    git -C "$REPO_DIR" pull
fi

echo "=== Installing code-py dependencies ==="

cd "$REPO_DIR/code-py"
uv sync

echo ""
echo "=========================================="
echo "Workspace ready!"
echo "=========================================="
echo ""
echo "  Repo:  $REPO_DIR"
echo "  Data:  $WORKSPACE/data/ankihub"
echo ""
echo "To run IRT training:"
echo "  cd $REPO_DIR/code-py"
echo "  uv run python -m memory_models.irt.v1.train"
echo ""
echo "To start the Aim experiment tracker:"
echo "  cd $REPO_DIR/code-py"
echo "  uv run aim up --host 0.0.0.0"
echo ""
echo "  Then open: https://<pod-id>-43800.proxy.runpod.net"
echo "  (Port 43800 must be exposed when creating the pod)"
echo ""
