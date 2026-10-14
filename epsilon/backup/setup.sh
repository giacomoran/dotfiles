#!/bin/bash
set -euo pipefail

# Set up epsilon's nightly restic backups to the NAS. Run as root, after the NAS's
# rest-server is running (see ../README.md → Backups). From the Mac:
#
#   tar --no-xattrs -C epsilon/backup -cf - . | ssh root@epsilon 'dir=$(mktemp -d) && tar -xf - -C "$dir" && bash "$dir/setup.sh" "$dir"'
#
# The files are streamed in rather than run from a copy in giacomoran's home,
# because anything there can be edited by agents, and this runs as root.

if [ "$#" -ne 1 ]; then
    echo "usage: setup.sh <directory with the backup files>" >&2
    exit 2
fi
source_dir="$1"

apt-get install -y restic sqlite3 apache2-utils

# Secrets, readable by root only, generated once. The repository password is the
# only way to read the backups: keep a copy outside epsilon (1Password).
install -d -m 700 /etc/restic
umask 077
if [ ! -s /etc/restic/epsilon.repository-password ]; then
    head -c 32 /dev/urandom | base64 | tr -d '=+/' | head -c 40 > /etc/restic/epsilon.repository-password
fi
if [ ! -s /etc/restic/epsilon.rest-password ]; then
    head -c 32 /dev/urandom | base64 | tr -d '=+/' | head -c 40 > /etc/restic/epsilon.rest-password
fi
# The NAS's rest-server checks this bcrypt hash; copy it into its data/.htpasswd
if [ ! -s /etc/restic/epsilon.htpasswd ]; then
    htpasswd -nbB epsilon "$(cat /etc/restic/epsilon.rest-password)" | head -1 > /etc/restic/epsilon.htpasswd
fi
umask 022

install -m 600 "$source_dir/excludes.txt" /etc/restic/epsilon.excludes
install -m 700 "$source_dir/epsilon-backup" /usr/local/sbin/epsilon-backup
for unit in epsilon-backup.service epsilon-backup.timer epsilon-backup-check.service epsilon-backup-check.timer; do
    install -m 644 "$source_dir/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload

# Create the repository on first run; rest-server allows that in append-only mode
export RESTIC_REPOSITORY="rest:http://nas-randazzo:8000/epsilon/"
export RESTIC_PASSWORD_FILE=/etc/restic/epsilon.repository-password
export RESTIC_REST_USERNAME=epsilon
RESTIC_REST_PASSWORD="$(cat /etc/restic/epsilon.rest-password)"
export RESTIC_REST_PASSWORD
if ! restic cat config > /dev/null 2>&1; then
    restic init
fi

systemctl enable --now epsilon-backup.timer epsilon-backup-check.timer
systemctl list-timers epsilon-backup.timer epsilon-backup-check.timer
