# .scripts

Python utilities for Giacomo's Obsidian vault. Run with `uv run python <script>.py` from this directory. Add dependencies with `uv add <pkg>`.

---

## Data and plots

**`datacenter_energy_plots.py`** — generates the data center energy constraint and HBM price plots embedded in wiki notes. Outputs PNGs to `Zxtra/Assets/`.

**`download_images.py`** — finds external image URLs in vault notes, opens a review UI (pywebview), and lets you download each image to `Zxtra/Assets/` with the markdown link rewritten to an Obsidian wikilink.

---

## Video and media

**`create_video_notes.py`** — transcribes a local video file with WhisperX and creates a note in `📘 Sources - Videos/`.

**`create_x_video_note.py`** — downloads a video from X (Twitter), transcribes it, and creates a note in `📘 Sources - Videos/`.

---

## Wiki knowledge graph

Tools for analysing the link structure of `👾 Wiki/`. All read the graph from `[[wikilinks]]` parsed out of every note. Run any of them without arguments to see usage.

**`network_common.py`** — shared graph loading and community detection; imported by the tools below, not run directly.

**`network-cliques.py`** — finds maximal cliques of size ≥ N in the undirected graph. A k-clique means k notes all linking to each other; a tree over the same notes needs only k-1 edges. Start here when pruning over-linked clusters — largest cliques have the highest ROI.

**`network-triangles.py`** — finds directed edges A→C that are redundant because A→B→C already exists. Sorted by redundancy ratio (mediators / out-degree of A) and annotated with k-core number so the densest-cluster offenders surface first.

**`network-reduction.py`** — computes the transitive reduction of the condensed graph, generalising triangle detection to paths of any length. Also reports mutual-link cycles (strongly connected components of size > 1).

**`network-bridge.py`** — samples cross-cluster note pairs with no current link for serendipity review. Re-run with different `--seed` values for a fresh draw each time.

**`network-holes.py`** — finds pairs of notes sharing N+ common neighbors but no direct link. Use `--cross-cluster` to restrict to pairs from different topic communities, which filters out same-cluster near-duplicates and surfaces genuine cross-domain bridge candidates.
