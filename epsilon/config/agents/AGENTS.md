When reading or writing code, always load and follow the `code` skill.

My shells (local and remote machines) are almost always fish, not bash.

Ask me before committing. Don't commit on my behalf unless I explicitly agree. This
applies even where a permission rule would let the commit through without a prompt.

Use subagents, including Claude Code ones through the CLI.

On epsilon (this Linux machine), start dev servers as usual, on `localhost`; `--host` isn't needed. My Mac forwards every port a server listens on here (1024 to 32767) to the same port on the Mac, so give me the `http://localhost:<port>` URL and it opens there. A port my Mac already uses isn't forwarded, so pick another port if I say the page shows something else.
