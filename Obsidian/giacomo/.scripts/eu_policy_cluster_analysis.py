"""
EU magnet policy cluster analysis.

Steps:
1. Identify notes in the cluster
2. Print external backlinks
3. Identify what root note should be
4. Print current cluster structure
5. Propose tree structure
"""

import re
import os
from pathlib import Path
from collections import defaultdict

WIKI = Path("/Users/giacomoran/Obsidian/giacomo/👾 Wiki")
ALL_VAULT = Path("/Users/giacomoran/Obsidian/giacomo")

# ── 1. Cluster definition ────────────────────────────────────────────────────

CLUSTER = {
    "Index - EU magnet policy",
    "China's April 2025 rare earth export controls caused a 75% drop in magnet shipments to Europe within weeks",
    "EU Critical Raw Materials Act sets non-binding 2030 benchmarks but creates legally binding permitting acceleration and recycled content mandates for NdFeB",
    "EU CRM funding introduces offtake conditionality requiring output to flow to the EU",
    "EU CRM strategy operates on a two-step delivery, with binding demand-side tools deferred to 2027 and beyond",
    "EU diplomatic partnerships for rare earths are mostly frameworks without operational rare earth supply commitments",
    "European automakers are responding to rare earth supply risk through alternative motor architectures rather than supply chain diversification alone",
    "European rare earth magnet recycling has three operational or near-operational projects but aggregate capacity remains under 1,000 tonnes per year",
    "EIB doubled critical raw materials lending capacity to 2 billion in 2025 with a dedicated CRM Task Force",
    "RESourceEU repackages existing EU instruments toward CRM rather than committing new fiscal capacity",
    "The EU magnet scrap export restriction closes the recycling feedstock arbitrage that pulls end-of-life magnets toward Chinese refiners",
    "The European Critical Raw Materials Centre is modeled on Japan's JOGMEC, signaling a shift to active EU industrial policy on CRMs",
    "UK rare earth strategy is more articulated than funded and faces a structural gap after USA Rare Earth acquired Less Common Metals",
    "LKAB Per Geijer is a by-product of active iron-ore mining but faces a 10-15 year timeline to first production",
    "Rare Earths Norway's Fen Complex is continental Europe's largest known REE deposit but targets only 800 tonnes NdPr per year from 2032",
    "REEtec is the first industrial-scale rare earth separation plant in Europe, targeting 720 tonnes NdPr per year",
    "Solvay La Rochelle is the largest rare earth separation facility outside China and is expanding into NdPr production",
    "Vacuumschmelze is the only Western producer of NdFeB magnets with established multi-country European production",
    "Neo Performance Materials produces 2,000 tonnes of sintered NdFeB per year at Narva, Estonia, fed by co-located Silmet separation",
    "Sovereign NdPr price floors are becoming a Western rare earth policy template",
    "NdFeB sintered magnet costs $110-175 per kg in Europe in 2026",
}


def extract_links(text: str) -> set[str]:
    """Extract [[wikilink]] titles from text."""
    return set(re.findall(r'\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]', text))


def read_note(title: str) -> str | None:
    p = WIKI / f"{title}.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


# ── 2. Build intra-cluster link graph ────────────────────────────────────────

# links_from[A] = set of cluster notes that A links to
links_from: dict[str, set[str]] = defaultdict(set)
# outbound_from[A] = set of non-cluster notes that A links to
outbound_from: dict[str, set[str]] = defaultdict(set)

for title in CLUSTER:
    text = read_note(title)
    if text is None:
        print(f"  [missing] {title}")
        continue
    for link in extract_links(text):
        if link in CLUSTER:
            links_from[title].add(link)
        else:
            outbound_from[title].add(link)

# ── 3. Find external backlinks ────────────────────────────────────────────────
# Scan entire vault for files that link to any cluster note

# Build a map: cluster_note → list of (source_file, source_title)
external_backlinks: dict[str, list[str]] = defaultdict(list)

md_files = list(ALL_VAULT.rglob("*.md"))
for fp in md_files:
    # Skip cluster notes themselves and system dirs
    rel = fp.relative_to(ALL_VAULT)
    stem = fp.stem
    if stem in CLUSTER:
        continue
    try:
        text = fp.read_text(encoding="utf-8")
    except Exception:
        continue
    links = extract_links(text)
    for target in links:
        if target in CLUSTER:
            external_backlinks[target].append(str(rel))

# ── PRINT ─────────────────────────────────────────────────────────────────────

print("=" * 70)
print("STEP 1 — CLUSTER NOTES")
print("=" * 70)
for t in sorted(CLUSTER):
    exists = (WIKI / f"{t}.md").exists()
    print(f"  {'✓' if exists else '✗'} {t}")

print()
print("=" * 70)
print("STEP 2 — EXTERNAL BACKLINKS (from outside cluster)")
print("=" * 70)
all_external_sources: set[str] = set()
for target in sorted(external_backlinks):
    sources = sorted(set(external_backlinks[target]))
    all_external_sources.update(sources)
    print(f"\n  → [[{target}]]")
    for s in sources:
        print(f"       ← {s}")

print()
print(f"  Total unique external source files: {len(all_external_sources)}")

print()
print("=" * 70)
print("STEP 3 — CURRENT INTRA-CLUSTER LINK GRAPH")
print("=" * 70)
print("  (A → B means A links to B within the cluster)")
for src in sorted(links_from):
    for tgt in sorted(links_from[src]):
        print(f"  {src}  →  {tgt}")

# Compute in-degree from outside the cluster
print()
print("=" * 70)
print("STEP 4 — EXTERNAL IN-DEGREE PER NOTE")
print("  (how many external files link to each cluster note)")
print("=" * 70)
ext_indegree = {t: len(set(external_backlinks.get(t, []))) for t in CLUSTER}
for title, deg in sorted(ext_indegree.items(), key=lambda x: -x[1]):
    if deg > 0:
        print(f"  {deg:3d}  {title}")

print()
print("  Notes with zero external backlinks:")
for title in sorted(CLUSTER):
    if ext_indegree[title] == 0:
        print(f"       {title}")

print()
print("=" * 70)
print("STEP 5 — PROPOSED TREE STRUCTURE (see below)")
print("=" * 70)
