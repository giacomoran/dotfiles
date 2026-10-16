# Disable the fish greeting
set fish_greeting

# Set the default language
# https://unix.stackexchange.com/q/87745
# https://unix.stackexchange.com/q/576701
set -gx LANG en_US.UTF-8
set -gx GITHUB_USER giacomorandazzo

# Add common binary directories to PATH (for uv, cargo, etc.)
fish_add_path --global ~/.cargo/bin
fish_add_path --global ~/.local/bin

# Add mise shims to PATH so node, npm and pnpm work in non-interactive shells too
fish_add_path --global ~/.local/share/mise/shims

# Let Vite-based dev servers started with --host answer at http://epsilon:<port>
# (same value as ~/.config/environment.d/999-dev-servers.conf, which covers T3 Code)
set -gx __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS epsilon,epsilon.tail52f04e.ts.net

# Make MuJoCo render through EGL, since there is no display
# (same value as ~/.config/environment.d/999-mujoco.conf, which covers T3 Code)
set -gx MUJOCO_GL egl

# Make glibc hand freed memory back to the system
# (same values as ~/.config/environment.d/999-malloc.conf, which covers T3 Code)
set -gx MALLOC_ARENA_MAX 2
set -gx MALLOC_TRIM_THRESHOLD_ 65536

# Use `less` as default pager
# See below for configuration options
set -gx PAGER less

# `less`: Set default options
# -i/--ignore-case         search case-insensitively if pattern is lower-cased
# -R/--RAW-CONTROL-CHARS   display raw control characters for colors and hyperlinks
# -F/--quit-if-one-screen  print instead of paginate if the file is small enough
# -j/--jump-target         specify where to position a target line (either as number of rows or as percentage of screen height)
# -#/--shift               specify how much to scroll horizontally (either as number of cols or as percentage of screen width)
set -gx LESS "-iRFj.2#.2"

# `less`: Don't save history
set -gx LESSHISTFILE -

# Use `bat` to view man pages (or batcat on Ubuntu)
# https://github.com/sharkdp/bat#man
if type -q bat
    set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
else if type -q batcat
    set -gx MANPAGER "sh -c 'col -bx | batcat -l man -p'"
end

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if status is-interactive
    # Aliases
    alias which="type -a"
    alias ls="eza --icons --across"
    alias ll="eza --icons --long --header --git --all"
    alias la="eza --icons --across --all"
    alias tree="tree -I '__pycache__|node_modules|*.pyc|.git|.venv|venv|.mypy_cache|.pytest_cache|.ruff_cache|dist|build|*.egg-info|.tox|.coverage|.ipynb_checkpoints'"

    # Abbreviations
    abbr --add --global gs 'git status'
    abbr --add --global ga 'git add'
    abbr --add --global gc 'git commit -m'
    abbr --add --global gl 'git log'
    abbr --add --global gst 'git show-tree' # from git-extras

    # Activate starship
    if type -q starship
        starship init fish | source
    end

    # Activate direnv
    if type -q direnv
        direnv hook fish | source
    end

    # Activate mise, so `mise use` and per-project tool versions apply immediately
    if type -q mise
        mise activate fish | source
    end

    # Autostart zellij only for SSH logins, not for terminals opened inside T3 Code
    if type -q zellij; and set -q SSH_CONNECTION
        eval (zellij setup --generate-auto-start fish | string collect)
    end
end
