#!/bin/bash
set -euo pipefail

# Forget and prune old snapshots in epsilon's restic repository on the NAS.
#
# epsilon backs up through the NAS's rest-server in append-only mode, so it can add
# snapshots but never delete them. Thinning them out happens here instead, over
# SFTP straight to the repository's files. Run it every month or two.
#
# Needs the repository password in 1Password as "restic epsilon" (password field);
# it lives on epsilon in /etc/restic/epsilon.repository-password.

export RESTIC_REPOSITORY="sftp:giacomoran@nas-randazzo:/home/rest-server/data/epsilon"
export RESTIC_PASSWORD_COMMAND="op read 'op://Personal/restic epsilon/password'"

restic forget --host epsilon --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune
