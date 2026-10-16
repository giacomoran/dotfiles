#!/bin/bash
set -e

export RESTIC_REPOSITORY="sftp:giacomoran@nas-randazzo:/restic"
export RESTIC_PASSWORD_COMMAND="op read 'op://Personal/6uke4emlexwt26zux3qlo36vta/fff5ynrdqswbwaatb4ilh4npma'"
EXCLUDE="--exclude-file=$HOME/.config/restic/excludes.txt --exclude-caches"

# Run one chunk at a time: ./backup-chunked.sh 1
case "${1:-1}" in
  1) echo "Chunk 1: Documents, Desktop, Downloads"
     caffeinate -i restic backup $EXCLUDE ~/Documents ~/Desktop ~/Downloads ;;
  2) echo "Chunk 2: Pictures, Movies, Music"
     caffeinate -i restic backup $EXCLUDE ~/Pictures ~/Movies ~/Music ;;
  3) echo "Chunk 3: Developer/code folders"
     caffeinate -i restic backup $EXCLUDE ~/Developer ~/Projects ~/Code ~/src 2>/dev/null || true ;;
  4) echo "Chunk 4: Everything else"
     caffeinate -i restic backup $EXCLUDE ~ ;;
  prune) echo "Pruning old snapshots"
     restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune ;;
  *) echo "Usage: $0 {1|2|3|4|prune}" ;;
esac
