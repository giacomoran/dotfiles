#!/bin/sh
# Start restic's rest-server for epsilon's backups, unless it is already running.
#
# It listens on 127.0.0.1 only. The NAS runs Tailscale in userspace mode, which
# forwards tailnet connections to localhost, so the server is reachable over
# Tailscale but not from the home network.
#
# --append-only: clients can add snapshots but never delete or overwrite data, so
# a compromised client can't wipe its backups. Prune from a machine with SFTP
# access to data/ instead.
# --private-repos: each htpasswd user can only reach the repository named after it.
#
# Run it from DSM Task Scheduler at boot and every hour.
dir="$(cd "$(dirname "$0")" && pwd)"
pid_file="$dir/rest-server.pid"

if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    exit 0
fi

nohup "$dir/bin/rest-server" \
    --path "$dir/data" \
    --listen 127.0.0.1:8000 \
    --append-only \
    --private-repos \
    >> "$dir/rest-server.log" 2>&1 &
echo $! > "$pid_file"
