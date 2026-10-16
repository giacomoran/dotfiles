#!/bin/bash
set -euo pipefail

# Copy the vault's files over 5 MB between the Mac and epsilon, once a day.
#
# Obsidian Sync (Standard plan) skips files over 5 MB, logging "File too large to sync" once,
# so these files only reach epsilon (and come back from it) through this script. It only adds
# and updates files: renames and deletes don't carry over, and leave the old copy behind on the
# other side. Dot-folders (.obsidian, .scripts, .trash) are skipped, and so is 🛰️ Relay, which
# Relay syncs.

VAULT="$HOME/Obsidian/giacomo"
HOST_REMOTE="epsilon"
VAULT_REMOTE="Obsidian/giacomo"

notify_failure() {
  local msg="$1"
  osascript -e "display notification \"$msg\" with title \"Obsidian Large Files Failed\" sound name \"Basso\"" 2>/dev/null || true
  echo "[ERROR] $(date '+%Y/%m/%d %H:%M:%S') $msg" >&2
}

trap 'notify_failure "Sync failed — check ~/.config/obsidian-large-files/sync.log"' ERR

# Same filters both ways: files of at least 5 MB, newer side wins, no empty folders created.
# Only contents and modification times are copied, since permissions differ between the two.
# Symlinks are skipped: Obsidian Sync copies their targets as regular files (👾 Wiki/CLAUDE.md)
RSYNC_OPTIONS=(
  --recursive
  --times
  --omit-dir-times
  --update
  --min-size=5MB
  --prune-empty-dirs
  --exclude=".*"
  --exclude="/🛰️ Relay/"
  --itemize-changes
)

# Mac → epsilon, then epsilon → Mac (agents on epsilon download large PDFs too)
rsync "${RSYNC_OPTIONS[@]}" "$VAULT/" "$HOST_REMOTE:$VAULT_REMOTE/"
rsync "${RSYNC_OPTIONS[@]}" "$HOST_REMOTE:$VAULT_REMOTE/" "$VAULT/"

echo "[OK] $(date '+%Y/%m/%d %H:%M:%S') Sync completed successfully"
