#!/bin/bash
set -euo pipefail

export RESTIC_REPOSITORY="sftp:giacomoran@nas-randazzo:/restic"
export RESTIC_PASSWORD_COMMAND="security find-generic-password -a giacomoran -s restic-backup -w"

notify_failure() {
  local msg="$1"
  osascript -e "display notification \"$msg\" with title \"Restic Backup Failed\" sound name \"Basso\"" 2>/dev/null || true
  echo "[ERROR] $(date '+%Y/%m/%d %H:%M:%S') $msg" >&2
}

trap 'notify_failure "Backup failed — check ~/.config/restic/backup.log"' ERR

restic unlock --remove-all 2>/dev/null || true

# Backup (exit 3 = some files unreadable, treat as warning not failure)
restic backup \
  --exclude-file="$HOME/.config/restic/excludes.txt" \
  --exclude-caches \
  "$HOME" || { [[ $? -eq 3 ]] && echo "[WARN] $(date '+%Y/%m/%d %H:%M:%S') Some files could not be read" || exit 1; }

# Keep: 7 daily, 4 weekly, 6 monthly snapshots
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

echo "[OK] $(date '+%Y/%m/%d %H:%M:%S') Backup completed successfully"
osascript -e 'display notification "Backup completed successfully" with title "Restic Backup"' 2>/dev/null || true
