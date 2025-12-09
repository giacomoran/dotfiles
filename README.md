# Remote setup

This repository contains configuration files for setting up remote instances.

Design decisions:

- Each remote setup has its own folder (e.g., `general/`). We prefer **duplication over abstraction** for maximum flexibility—each setup can be customized independently without affecting others. Modern AI tools make maintaining duplicated code easier, and this approach ensures each setup remains portable and self-contained.
- **Separation between `cloud-init.yaml` and `bootstrap.sh`**: We keep `cloud-init.yaml` minimal, handling only infrastructure-level setup (user creation, SSH keys, networking/VPN). Custom configuration and package installation is pushed to `bootstrap.sh` for maximum portability. This allows `bootstrap.sh` to run in environments that don't support cloud-init, in Docker containers nested within VMs, or manually via SSH—making it work across the inconsistent landscape of GPU cloud providers and remote instance setups.
