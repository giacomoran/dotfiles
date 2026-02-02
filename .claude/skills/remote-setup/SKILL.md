---
name: remote-setup
description: Set up remote environments by exploring ~/Projects/dotfiles-remote/<env>/ and running the appropriate scripts via SSH. Usage: /remote-setup <env> <ssh-string> [version]. Dynamically discovers workflow from scripts in the environment directory. Use when setting up RunPod, Prime Intellect, AMD cloud, or any other remote environment defined in dotfiles-remote.
allowed-tools: Bash(ssh:*), Bash(cat:*), Bash(ls:*), Read, Glob
---

# Remote Setup Skill

Set up remote development environments by dynamically discovering and executing scripts from `~/Projects/dotfiles-remote/<env>/`.

## Arguments

```
/remote-setup <env> <ssh-string> [version]
```

- `<env>`: Environment name (directory under `dotfiles-remote/`, e.g., `runpod`, `lerobot-runpod`, `lerobot-prime-intellect`, `lerobot-amd`)
- `<ssh-string>`: SSH connection string from provider (e.g., `ssh root@1.2.3.4 -p 12345`)
- `[version]`: Optional version tag for LeRobot checkout (e.g., `v0.5.0`)

## Workflow

### Phase 1: Parse Arguments and Validate

1. Extract environment name, SSH connection string, and optional version from arguments
2. Validate the environment directory exists at `~/Projects/dotfiles-remote/<env>/`
3. Parse SSH string to extract:
   - User (e.g., `root` or `giacomoran`)
   - Host
   - Port (if specified with `-p`)
   - **Strip `-i <path>`** if present (providers like RunPod include spurious identity file options; we use 1Password SSH agent instead)

### Phase 2: Discover Environment Scripts

Explore the environment directory to understand the workflow:

```bash
ls -la ~/Projects/dotfiles-remote/<env>/
```

Read each script file to understand:

- **Purpose**: What the script does (from comments and content)
- **Execution context**: Which user it expects (root vs regular user)
- **Dependencies**: What must run before it
- **Order**: Determine execution sequence

**Common patterns to detect:**

| File                     | Typical Purpose                             | Runs As           |
| ------------------------ | ------------------------------------------- | ----------------- |
| `cloud-init.yaml`        | VM provisioning (warn user, assume deployed) | N/A              |
| `bootstrap.sh`           | Initial root setup (creates user, SSH keys) | root              |
| `setup.sh`               | User environment setup (shell, tools)       | user (giacomoran) |
| `bootstrap-user.sh`      | Alternative name for user setup             | user (giacomoran) |
| `setup-lerobot.sh`       | LeRobot framework installation              | user              |
| `bootstrap-container.sh` | Container-specific setup                    | user              |

**Detection logic:**

- Check script headers for comments indicating purpose
- Look for `id -u` checks (root vs user detection)
- Look for `su - giacomoran` or similar (user switch needed)
- Look for mentions of `lerobot`, `hf auth login`, `wandb login`

### Phase 3: Build Execution Plan

Based on script analysis, create an execution plan:

1. Identify which scripts need to run
2. Determine order (bootstrap before setup, etc.)
3. Identify user context for each script
4. If `cloud-init.yaml` exists, warn user to ensure it was deployed — then proceed (assume VM is ready)

### Phase 4: Execute via SSH

For each script in the execution plan:

1. **Build SSH command** with appropriate options (no identity file — uses 1Password SSH agent):

   ```bash
   ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 <user>@<host> -p <port>
   ```

2. **Switch user if needed**: If script expects different user than SSH connection:
   - If connected as root but script needs user: rebuild SSH with `giacomoran@host`
   - Or use `su - giacomoran -c "command"`

3. **Execute script** with extended timeout for long operations:

   ```bash
   ssh <options> "curl -fsSL <raw-github-url> | bash"
   ```

   Use timeout of 600000ms (10 minutes) for scripts that install PyTorch or large packages.

4. **Check exit status** after each script. If failure:
   - Report the error
   - Ask user if they want to retry or skip

### Phase 5: Handle LeRobot Version (if provided)

If a version argument was provided AND a lerobot-related script was detected:

After the main scripts complete, checkout the specified version:

```bash
ssh <user-connection> "cd ~/lerobot && git fetch --tags && git checkout <version>"
```

Then reinstall:

```bash
ssh <user-connection> "cd ~/lerobot && ~/miniforge3/envs/lerobot/bin/pip install -e ."
```

### Phase 6: Report Status and Manual Steps

After all scripts complete:

1. **Verify GPU** (if NVIDIA environment detected):

   ```bash
   ssh <user-connection> "python -c \"import torch; print(f'CUDA available: {torch.cuda.is_available()}')\""
   ```

2. **Report completion status**

3. **List manual steps** detected from scripts:
   - `hf auth login` - Hugging Face authentication
   - `wandb login` - Weights & Biases authentication
   - Any other interactive steps mentioned in script comments

## SSH Connection Helpers

### Parsing SSH String

Given: `ssh root@1.2.3.4 -p 12345 -i ~/.ssh/id_ed25519`

Extract and clean:
- Initial user: `root`
- Host: `1.2.3.4`
- Port: `12345` (default: 22)
- **Discard** `-i ~/.ssh/id_ed25519` (spurious; 1Password agent handles auth)

### Rebuilding for Different User

To switch from root to giacomoran:

```
ssh giacomoran@1.2.3.4 -p 12345
```

### Common SSH Options

Always include:

- `-o StrictHostKeyChecking=accept-new` - Accept new host keys automatically
- `-o ConnectTimeout=30` - Fail fast on connection issues

## Error Handling

| Error                           | Action                                          |
| ------------------------------- | ----------------------------------------------- |
| Environment directory not found | List available environments, ask user to choose |
| SSH connection failed           | Report error, suggest checking host/port/key    |
| Script failed (non-zero exit)   | Show output, ask to retry or continue           |
| Timeout on long operation       | Increase timeout, retry                         |

## Example Execution

For `/remote-setup lerobot-runpod ssh root@1.2.3.4 -p 12345 -i ~/.ssh/id_ed25519 v0.5.0`:

1. Parse: env=`lerobot-runpod`, host=`1.2.3.4`, port=`12345`, version=`v0.5.0` (strip `-i` flag)
2. Explore `~/Projects/dotfiles-remote/lerobot-runpod/`:
   - `bootstrap.sh` - runs as root, creates user
   - `setup.sh` - runs as giacomoran, installs tools
   - `setup-lerobot.sh` - runs as giacomoran, installs LeRobot
3. Execute:
   - SSH as root, run bootstrap.sh
   - SSH as giacomoran, run setup.sh
   - SSH as giacomoran, run setup-lerobot.sh
4. Checkout v0.5.0 and reinstall LeRobot
5. Verify GPU, report manual steps (hf/wandb login)

## Notes

- **1Password SSH agent**: We don't use identity files; strip `-i <path>` from provider SSH strings (RunPod and others include spurious `-i ~/.ssh/id_ed25519`)
- Scripts are fetched from GitHub raw URLs (the repo must be pushed)
- The skill dynamically adapts to new environments added to dotfiles-remote
- If `cloud-init.yaml` present, warn user to confirm it was deployed — then proceed
- Always test SSH connectivity before running scripts
