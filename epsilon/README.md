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

   Dev servers stay on epsilon's `localhost`; open them in a T3 browser tab in an epsilon project, which runs on epsilon and streams to the app.

## BIOS settings

- Advanced → AMD CBS → FCH Common Options → AC Power Loss Options → Always On (starts by itself after a power cut)
- Fan curve (Advanced → Pc Health Status) left at defaults

## Notes

- The network config from the installer had no `dhcp4: true`, so the box only got IPv6 and could not reach GitHub. Fixed with `netplan set ethernets.enp1s0.dhcp4=true && netplan apply`.
- The Wi-Fi card (Intel AX200) sometimes fails to start after a warm reboot. A full power-off fixes it. Ethernet is the main connection anyway.
- Ubuntu sees ~26 GB of RAM because the integrated GPU reserves ~6 GB. Lowering the UMA frame buffer size in the BIOS (Chipset tab) would return some of it.
