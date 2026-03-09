---
name: obsidian
description: Work with the Obsidian CLI (`obsidian` command). Use when reading, writing, searching, or managing notes in an Obsidian vault from the terminal.
allowed-tools: Bash(obsidian:*)
---

# Obsidian CLI Skill

The `obsidian` CLI controls a running Obsidian app (launching it automatically if needed). All parameters use `key=value` syntax; values with spaces must be quoted.

## Vault Targeting

By default, commands operate on the active vault. Target a specific vault with `vault="Vault Name"`.

## File Operations

```sh
# List & browse
obsidian files                                   # all files
obsidian files folder=Projects/Active            # files in folder
obsidian files ext=md format=json                # JSON output
obsidian folders                                 # all folders
obsidian folders format=tree                     # tree view

# Read
obsidian read file="Note Name"                   # by wikilink name
obsidian read path="Projects/Note.md"            # by exact path

# Create
obsidian create name="New Note"
obsidian create name="Script" template="YouTube Script" path=Content/
obsidian create name="Note" --silent             # no confirmation
obsidian create name="Existing" --overwrite      # replace existing

# Edit
obsidian append file="Research" content="Text"   # add to end
obsidian prepend file="Inbox" content="Text"     # add to start
obsidian append file="Log" --inline              # no trailing newline

# Move & delete
obsidian move file="Draft" to=Archive/2026/      # preserves links
obsidian delete file="Old Note"                  # to trash
obsidian delete file="Old Note" --permanent      # irreversible
```

## Search

```sh
obsidian search query="topic"
obsidian search query="meeting" limit=20 format=json
obsidian search query="[tag:publish]"            # tag-based
obsidian search query="[status:active]"          # property-based
obsidian search:open query="[tag:review]"        # open results in app
```

## Daily Notes

```sh
obsidian daily                                   # open today's note
obsidian daily:read                              # read today's content
obsidian daily:read --copy                       # copy to clipboard
obsidian daily:append content="Text"
obsidian daily:prepend content="Text"
obsidian daily:open date=2026-02-15              # specific date
obsidian daily:path                              # get file path
```

## Properties (YAML Frontmatter)

```sh
obsidian properties file="Note"                  # read all properties
obsidian properties:set file="Draft" status=active
obsidian properties:set file="Article" published=2026-02-28 type=date
obsidian properties:set file="Video" tags="pkm,obsidian" type=tags
obsidian properties:remove file="Draft" key=draft
```

Property types: `text`, `list`, `number`, `checkbox`, `date`, `tags`

## Tags & Links

```sh
obsidian tags                                    # all tags
obsidian tags sort=count                         # by frequency
obsidian tag tagname=pkm                         # notes with tag
obsidian tags:rename old=meeting new=meetings    # bulk rename
obsidian links file="Note"                       # outgoing links
obsidian backlinks file="Note"                   # incoming links
obsidian unresolved                              # broken links
obsidian orphans                                 # unlinked notes
```

## Tasks

```sh
obsidian tasks                                   # all tasks
obsidian tasks format=json
obsidian task:create content="Do X"
obsidian task:create content="Do X" tags="work,urgent"
obsidian task:complete task=task-id
```

## Plugins & Themes

```sh
obsidian plugins                                 # list all
obsidian plugin:enable id=dataview
obsidian plugin:disable id=calendar
obsidian plugin:reload id=my-plugin             # dev reload
obsidian themes
obsidian theme:set name="Minimal"
obsidian snippets
obsidian snippet:enable name="custom-fonts"
```

## Sync & Publish

```sh
obsidian sync:status
obsidian sync:history file="Note"
obsidian sync:restore file="Note" version=3
obsidian publish:list
obsidian publish:add file="Ready Post"
obsidian publish:remove file="Outdated"
obsidian history file="Note"
obsidian history:restore file="Note" version=2
```

## Developer Commands

```sh
obsidian eval code="app.vault.getFiles().length" # execute JS
obsidian dev:screenshot path=~/Desktop/vault.png
obsidian dev:console limit=50
obsidian dev:errors
obsidian dev:css selector=".markdown-preview-view"
obsidian dev:dom selector=".workspace-leaf" total
```

## Output Formats

Append `format=<fmt>` to most commands:

| Format  | Output          |
| ------- | --------------- |
| `json`  | Structured data |
| `csv`   | Comma-separated |
| `md`    | Markdown        |
| `paths` | File paths only |
| `yaml`  | YAML            |
| `tree`  | Hierarchy       |
| `tsv`   | Tab-separated   |

## Common Flags

| Flag          | Meaning                     |
| ------------- | --------------------------- |
| `--silent`    | No confirmation prompt      |
| `--overwrite` | Replace existing file       |
| `--permanent` | Permanent delete (no trash) |
| `--copy`      | Copy output to clipboard    |
| `vault=Name`  | Target a specific vault     |
| `limit=N`     | Cap result count            |
| `sort=count`  | Sort results                |

## TUI Mode

Run `obsidian` with no arguments to launch the interactive file browser.

| Key      | Action                  |
| -------- | ----------------------- |
| `↑/↓`    | Move between files      |
| `Enter`  | Open in Obsidian        |
| `/`      | Search/filter           |
| `Esc`    | Clear search            |
| `n`      | New note                |
| `d`      | Delete                  |
| `r`      | Rename                  |
| `Tab`    | Autocomplete            |
| `Ctrl+R` | Reverse command history |
| `q`      | Quit                    |

## Obsidian URI Scheme

Use `obsidian://` URIs to open notes from scripts, browsers, or other apps.

```sh
# Open vault
open "obsidian://open?vault=MyVault"

# Open specific note
open "obsidian://open?vault=MyVault&file=Projects%2FNote"

# Search
open "obsidian://search?vault=MyVault&query=topic"

# Create new note
open "obsidian://new?vault=MyVault&name=NewNote&content=Hello"
open "obsidian://new?vault=MyVault&name=Note&append=true&content=More"
```

URI parameters must be percent-encoded (spaces → `%20`, `/` → `%2F`).
