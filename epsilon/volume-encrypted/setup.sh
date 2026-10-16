#!/bin/bash
set -euo pipefail

# Set up the encrypted volume, for client projects under NDA. Run as root. From the Mac:
#
#   tar --no-xattrs -C epsilon/volume-encrypted -cf - . | ssh root@epsilon 'dir=$(mktemp -d) && tar -xf - -C "$dir" && bash "$dir/setup.sh" "$dir"'
#
# Then encrypt it, typing a new passphrase: ssh -t root@epsilon volume-encrypted-format
#
# The files are streamed in rather than run from a copy in giacomoran's home,
# because anything there can be edited by agents, and this runs as root.

if [ "$#" -ne 1 ]; then
    echo "usage: setup.sh <directory with the volume-encrypted files>" >&2
    exit 2
fi
source_dir="$1"

for script in volume-encrypted-format volume-encrypted-unlock volume-encrypted-lock; do
    install -m 700 "$source_dir/$script" "/usr/local/sbin/$script"
done

# The volume takes the space left in the volume group after the root volume
if ! lvs ubuntu-vg/volume-encrypted > /dev/null 2>&1; then
    lvcreate -l 100%FREE -n volume-encrypted ubuntu-vg
fi

# While the volume is locked, its mount point refuses writes, so nothing meant for it
# lands on the unencrypted disk
if [ ! -d /mnt/volume-encrypted ]; then
    mkdir /mnt/volume-encrypted
    chmod 000 /mnt/volume-encrypted
    chattr +i /mnt/volume-encrypted
fi
