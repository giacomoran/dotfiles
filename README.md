# dotfiles

## dotfiles management

Git bare repository with `$HOME` as the work tree.

REFS: https://www.atlassian.com/git/tutorials/dotfiles

> Consider moving git work tree to root. Allows you to keep track of what system file you edit.
> Idea by Andrea, also found in https://mitxela.com/projects/dotfiles_management.

### Instructions

WARN: Make sure you add `—bar` to `git clone` otherwise you will overwrite the system.

Search for `$HOME` in the repo to look for files for which the home path variable
must be updated manually.

## Homebrew

All packages should be installed through Homebrew if possible.

A list of installed packages is in `$HOME/.config/Brewfile`.

Install the brewfile by running

```
brew bundle --file=~/.config/Brewfile
```

Update the brewfile by running

```
brew bundle dump --file=~/.config/Brewfile --force
```

Generate a Homebrew dependencies graph by running

```
brew graph --installed --highlight-leaves | fdp -T png -o graph.png
```

REFS:

- (Brew Bundle Brewfile Tips)[https://gist.github.com/ChristopherA/a579274536aab36ea9966f301ff14f3f]
- (Untangling Your Homebrew Dependencies)[https://blog.jpalardy.com/posts/untangling-your-homebrew-dependencies/]

## Fish

Use `command cat …` to run the un-aliased `cat` command

[fzf.fish](https://github.com/PatrickF1/fzf.fish) shortcuts:

- `Ctrl`+`Alt`+`F` to search for files or directory (descendants of current folder)
- `Ctrl`+`R` to search the command history
- `Ctrl`+`Alt`+`P` to search for processed

## QMK

My QMK keymaps can be found at: https://github.com/GiacomoRandazzo/qmk_firmware

ISSUE: `brew install qmk/qmk/qmk` is currently broken, but the workaround is to `brew install pkg-config`, see:

- https://github.com/qmk/homebrew-qmk/issues/53
- https://www.reddit.com/r/ErgoMechKeyboards/comments/10aay3q/comment/j700vr1/?utm_source=share&utm_medium=web2x&context=3

### Kyria

The Kyria uses an Elite-PI microcontroller, running `qmk flash` will not work.

```
qmk compile -kb kyria -km GiacomoRandazzo
qmk flash -c -kb kyria -km GiacomoRandazzo -e CONVERT_TO=elite_pi
```

REFS:

- https://docs.keeb.io/elite-pi-guide

## KMonad

If KMonad freezes run the commands:

```
kmonad-reinstall-drivers
kmonad-activate-drivers
```

REFS:

- https://github.com/kmonad/kmonad/issues/334#issuecomment-1000106276

Follow guide at first link, but switch to the `keycode-refactor` branch first.
When compiling remove `—system-ghc`.
Make sure no karabiner items in Settings > Privacy & Security > Input Monitoring are present.

The KMonad keyboard config is in `~/.config/kmonad/mbp.kbd`.
Activate with `sudo kmonad ~/.config/kmonad/mbp.kbd`.

Alternative tools to keep an eye on: [keyd](https://github.com/rvaiya/keyd), [𝑥MK](https://github.com/manna-harbour/xmk), [kanata](https://github.com/jtroo/kanata).

## Keyboard dead keys / broken `Option-*` shortcuts

In the `ABC` default keyboard layout, the `Option` key (both left and right)
activates a layer when held. The layer contains special keys, symbols and dead
keys.

The layer interferes with home row mods.
Moreover the dead keys are handled at the system level and make some shortcuts
unusable in terminal emulators. E.g. the `G` key corresponds to a dead key,
the `micro` editor's shortcut `Alt-G` does not work in `alacritty` with
`option_as_alt: Both`.

Solved by using a keyboard layout with no dead keys, see `Library/Keyboard Layouts
/US No Dead Keys.bundle`.

## Refs:

- https://github.com/iandunn/dotfiles/tree/abea232c46951ed368e58666471a4e4e0d182e64/keyboards/US%20No%20Dead%20Keys
- https://github.com/fabi1cazenave/kalamine

## Trackpad

I use natural scrolling.

I'd love to use only three and four finger gestures to free up panning with two fingers in the browser.
ISSUE: This is blocked because the three finger "Swipe between pages" gesture does not support natural scrolling in MacOS. Using two fingers instead.

## `sudo` with TouchID

REFS:

- https://github.com/fabianishere/pam_reattach
- https://derflounder.wordpress.com/2017/11/17/enabling-touch-id-authorization-for-sudo-on-macos-high-sierra/

Make sure you set the Homebrew path to `pam_reattach.so`.
If you get locked out use `su -` to fix the /etc/pam.d/sudo file (might need https://support.apple.com/en-us/HT204012)

NOTE:
This is required by the Hammerspoon KMonad setup.
After each MacOS update, the /etc/pam.d/sudo file is reset, you need to run `sudo cp /etc/pam.d/sudo{_new,}` to restore it.

## Raycast

Raycast picks up `sh` scripts in "Script Directories" with the necessary metadata.

To add a script directory, go to Raycast Settings > Extensions > + > Add Script Directory.

Add `.local/bin` as script directory to write scripts once that can be use in Raycast
and in the terminal.

REFS:

- https://github.com/raycast/script-commands
- (seach quicklinks) https://siboehm.com/articles/22/tools-I-like

The Raycast settings are expoted in `.config/Raycast.rayconfig`, they are
password protected.

## Podman / Docker

Runnind Docker.<br/>
I'd rather run Podman but `act` does not support Podman https://github.com/nektos/act/issues/303.

## Logseq

Currently setting up Logseq sync with GitHub. In iPhone we use the [a-shell](https://github.com/holzschu/a-shell) app with shortcuts.

FIX:

- a-shell does not currently support `ssh-agent`, we've instead created a passwordless ssh key and added it to GitHub as [deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#deploy-keys) (has read/write permission only to the GiacomoRandazzo/logseq repo).
  Tracking: https://github.com/holzschu/a-shell/issues/560
- When Logseq cloud based sync becomes more reliable switch to that

Refs:

- https://github.com/CharlesChiuGit/Logseq-Git-Sync-101
- https://discuss.logseq.com/t/sync-logseq-between-ios-and-pc-with-git/10854

## 1Password

Use 1Password to store dev secrets and SSH keys.

Refs:

- https://developer.1password.com/

## Anaconda

Using `miniconda`.

In a project folder:

- create [environment.yml](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually)
- add to `.envrc`: `layout anaconda ./environment.yml`

## Tricks

- **Download Github folders** Open in `github.dev` (navigate to the folder and press `.`).
  Select the folder in the VSCode sidebar, right click and `Download`.
- **Finder: Resize all culumns** Hold [⌥] to resize all columns at the same time.
- **Finder: shortcut for cutting and pasting** Copy with [⌘][c] then move with [⌘][⌥][V]
- **Symbols and other special chars** (This does not work in the `U.S. No Dead Keys Layout`) From the settings, open the accessibility virtual keyboard and hold [⌥] to view all the special symbols you can insert:
  - • is [⌥][8]
  - — (mdash) is [⌘][⇧][-]
  - `brew install bluesnooze` to prevent bluetooth connections to wake up the system after "Sleep"
