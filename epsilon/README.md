# epsilon

Always-on home server at my parents' house that runs T3 Code and coding agents.

- Trigkey S5 mini PC: Ryzen 7 5800H (8C/16T), 2 × 16 GB DDR4, Crucial P3 Plus 500 GB NVMe
- Ubuntu Server 26.04, reachable only over Tailscale (`ssh epsilon`, `ssh root@epsilon`)
- Disk: LVM, `ubuntu-lv` (350 GB, `/`) plus ~112 GB free in `ubuntu-vg` for an encrypted volume for NDA client projects

Unlike `general/`, there is no `cloud-init.yaml`: the OS was installed by hand from a USB stick, and `giacomoran` keeps a sudo password. Root-level setup runs as root over Tailscale SSH instead, so it is split from the user-level setup.

## Setup

1. Install Ubuntu Server: user `giacomoran`, OpenSSH server, no featured snaps.
2. At the console, join the tailnet, then disable key expiry for epsilon in the Tailscale admin console:

   ```sh
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --ssh
   ```

3. From the Mac, run the root bootstrap:

   ```sh
   ssh root@epsilon 'bash -s' < epsilon/bootstrap-root.sh
   ```

4. From the Mac, copy this folder over and run the user bootstrap:

   ```sh
   ssh giacomoran@epsilon 'mkdir -p ~/.dotfiles-remote/epsilon'
   rsync -a --delete epsilon/ giacomoran@epsilon:~/.dotfiles-remote/epsilon/
   ssh giacomoran@epsilon 'bash ~/.dotfiles-remote/epsilon/bootstrap.sh'
   ```

5. Log in interactively on epsilon (`ssh epsilon`):

   ```sh
   gh auth login
   claude          # then /login
   codex login --device-auth
   t3 pair --tailscale
   ```

   Open the pairing link from `t3 pair --tailscale` on the Mac to add epsilon as an environment in T3 Code.

6. From the Mac, let T3's browser start. Ubuntu blocks the sandbox its headless Chrome runs in, so browser tabs and HTML previews stay blank until an AppArmor profile allows it:

   ```sh
   ssh root@epsilon '/home/giacomoran/.local/bin/t3 browser setup'
   ```

7. Set up backups, see [Backups](#backups).
8. Set up the Obsidian vault, see [Obsidian](#obsidian).

## Dev servers

Start them with `--host` (e.g. `pnpm dev --host`) and open `http://epsilon:<port>` from the Mac or phone. The firewall (`ufw`, from `bootstrap-root.sh`) only accepts connections over Tailscale, whose access rules limit epsilon to my devices, so they stay off the home network. Vite rejects unknown host names; `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS` (set by `bootstrap.sh` for T3 Code and fish) adds epsilon's tailnet names for every project. The agent instructions on epsilon say to use `--host`.

T3 browser tabs in an epsilon project also reach `localhost` on epsilon, but they stream a headless Chrome and feel laggy; they suit agents checking their own work.

Docker's published ports bypass `ufw`: publish them on `127.0.0.1` only.

## Obsidian

The vault lives in `~/Obsidian/giacomo`, so agents on epsilon can work on it. [Obsidian Headless](https://obsidian.md/help/sync/headless) (`ob`) syncs it through Obsidian Sync without the app, as one more Sync device; `obsidian-sync.service` runs `ob sync --continuous`. Plugins don't run, so the Relay folders only update through Obsidian Sync, and dot-folders like `.claude/` don't sync at all.

Setting it up (`bootstrap.sh` installs `ob` and the service), interactively on epsilon:

```sh
ob login
ob sync-list-remote   # shows the remote vault's name
ob sync-setup --vault <name> --path ~/Obsidian/giacomo --device-name epsilon
ob sync --path ~/Obsidian/giacomo
systemctl --user enable --now obsidian-sync.service
```

`sync-setup` asks for the vault's end-to-end encryption password, if it has one. The first `ob sync` downloads the whole vault; the service takes over from there.

## Backups

Nightly restic backups to the NAS (`nas-randazzo`), with a weekly check:

- **NAS side:** restic's [rest-server](https://github.com/restic/rest-server) runs under my NAS account from `~/rest-server` (start script: `nas/rest-server-start.sh`). It listens on `127.0.0.1:8000`; the NAS runs Tailscale in userspace mode, which forwards tailnet connections to localhost, so it's reachable over Tailscale but not from the home network. `--append-only` means epsilon can add snapshots but never delete them, so a compromised epsilon can't wipe its backups. `--private-repos` keeps epsilon's login to its own repository.
- **epsilon side:** `backup/` holds `epsilon-backup` (run by `epsilon-backup.timer` at 03:30 and `epsilon-backup-check.timer` on Sundays) and the excludes. It backs up `/home/giacomoran`, `/etc`, `/root` and consistent SQLite snapshots of T3 Code's databases, minus rebuildable toolchains, caches and build output, and minus login tokens and private keys. Secrets live in `/etc/restic`, root-only, so agents running as `giacomoran` can't read or touch the backups.
- **Pruning:** from the Mac, with `~/.config/restic/prune-epsilon.sh`, over SFTP straight to the repository's files.

Setting it up:

1. On the NAS, put the rest-server binary (`linux_armv7` release) in `~/rest-server/bin/` and `nas/rest-server-start.sh` as `~/rest-server/start.sh`.
2. In DSM → Control Panel → Task Scheduler, create two tasks running `/var/services/homes/giacomoran/rest-server/start.sh` as `giacomoran`: a triggered task on boot-up, and a scheduled task every hour (it exits if the server is already running).
3. From the Mac, run the setup on epsilon. It installs restic, generates the secrets once, and creates the repository:

   ```sh
   tar --no-xattrs -C epsilon/backup -cf - . | ssh root@epsilon 'dir=$(mktemp -d) && tar -xf - -C "$dir" && bash "$dir/setup.sh" "$dir"'
   ```

   On the first run, copy epsilon's login hash into the NAS's htpasswd before the setup creates the repository: `ssh root@epsilon cat /etc/restic/epsilon.htpasswd | ssh nas-randazzo 'umask 077; cat > ~/rest-server/data/.htpasswd'`.
4. Store the repository password in 1Password as "restic epsilon": `ssh root@epsilon cat /etc/restic/epsilon.repository-password`. Without it the backups can't be read.

Restoring, on epsilon as root: `epsilon-backup` sets the repository up from `/etc/restic`; for a one-off restore, export the same variables and run `restic restore latest --target /tmp/restore --include <path>`. If epsilon is gone, restore from the Mac over SFTP: `restic -r sftp:giacomoran@nas-randazzo:/home/rest-server/data/epsilon restore …` with the password from 1Password.

## BIOS settings

- Advanced → AMD CBS → FCH Common Options → AC Power Loss Options → Always On (starts by itself after a power cut)
- Fan curve (Advanced → Pc Health Status) left at defaults

## Notes

- The network config from the installer had no `dhcp4: true`, so the box only got IPv6 and could not reach GitHub. Fixed with `netplan set ethernets.enp1s0.dhcp4=true && netplan apply`.
- The Wi-Fi card (Intel AX200) sometimes fails to start after a warm reboot. A full power-off fixes it. Ethernet is the main connection anyway.
- Ubuntu sees ~26 GB of RAM because the integrated GPU reserves ~6 GB. Lowering the UMA frame buffer size in the BIOS (Chipset tab) would return some of it.
