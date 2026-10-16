"""
Serendipity tools for the wiki knowledge graph.

Parses [[links]] from all wiki notes, builds a directed graph, and runs
several analyses for manual review:

  triangles   — edges A→C redundant because A→B→C already exists
                sorted by redundancy ratio (mediators / out-degree of A)
  cliques     — maximal cliques of size ≥ N (higher-order over-linking)
  reduction   — transitive reduction: all inter-note edges covered by longer
                paths, plus mutual-link cycles (SCCs)
  bridge      — cross-cluster note pairs with no current link (serendipity)
  holes       — pairs sharing N+ common neighbors but no direct link

Usage:
    uv run python serendipity.py triangles [--min-mediators N]
    uv run python serendipity.py cliques [--min-size N]
    uv run python serendipity.py reduction
    uv run python serendipity.py bridge [--count N] [--seed S]
    uv run python serendipity.py holes [--min-shared N] [--cross-cluster] [--seed S]
"""

import argparse
import random
import re
from pathlib import Path

import networkx as nx

VAULT_PATH = Path(__file__).parent.parent
WIKI_DIR = VAULT_PATH / "👾 Wiki"

# Structural files: exclude from graph nodes and link sources
EXCLUDE_NAMES = {"Index.md", "Log.md", "CLAUDE.md"}

# Matches [[Note Title]], [[Note Title#section]], [[Note Title|alias]]
# Captures only the note title (group 1), stripping anchors and aliases
LINK_PATTERN = re.compile(r'\[\[([^\]|#\n]+?)(?:[#|][^\]\n]*)?\]\]')


# ── Graph loading ─────────────────────────────────────────────────────────────

def load_graph() -> nx.DiGraph:
    graph = nx.DiGraph()

    # First pass: register all note titles as nodes
    notes: dict[str, Path] = {}
    for path in WIKI_DIR.glob("*.md"):
        if path.name in EXCLUDE_NAMES:
            continue
        title = path.stem
        notes[title] = path
        graph.add_node(title)

    # Second pass: extract [[links]] and add directed edges
    for title, path in notes.items():
        text = path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            target = match.group(1).strip()
            if target in notes and target != title:
                graph.add_edge(title, target)

    return graph


def detect_communities(graph: nx.DiGraph, seed: int) -> dict[str, int]:
    """Return {note_title: community_id} for the largest connected component."""
    undirected = graph.to_undirected()
    largest_cc = max(nx.connected_components(undirected), key=len)
    subgraph = undirected.subgraph(largest_cc)
    random.seed(seed)
    communities = list(nx.algorithms.community.label_propagation_communities(subgraph))
    node_to_community: dict[str, int] = {}
    for i, community in enumerate(communities):
        for node in community:
            node_to_community[node] = i
    return node_to_community


# ── triangles ─────────────────────────────────────────────────────────────────

def cmd_triangles(graph: nx.DiGraph, min_mediators: int) -> None:
    """Find edges A→C redundant because A→B→C already exists.

    Sorted by redundancy ratio = mediators / out-degree(A), so a node that
    has most of its out-edges covered ranks higher than a large hub with a
    few covered edges.
    """
    core_number = nx.core_number(graph.to_undirected())

    redundant: list[tuple[str, str, list[str], float]] = []

    for a, c in graph.edges():
        mediators = [
            b for b in graph.successors(a)
            if b != c and graph.has_edge(b, c)
        ]
        if len(mediators) < min_mediators:
            continue
        out_degree = graph.out_degree(a)
        ratio = len(mediators) / out_degree if out_degree > 0 else 0.0
        redundant.append((a, c, mediators, ratio))

    if not redundant:
        print(f"No redundant edges found with {min_mediators}+ mediators.")
        return

    redundant.sort(key=lambda x: x[3], reverse=True)

    print(f"Found {len(redundant)} edges with {min_mediators}+ mediators (sorted by redundancy ratio):\n")
    for a, c, mediators, ratio in redundant:
        core_a = core_number.get(a, 0)
        core_c = core_number.get(c, 0)
        via = ", ".join(f"[[{b}]]" for b in mediators[:3])
        suffix = f" (+{len(mediators) - 3} more)" if len(mediators) > 3 else ""
        print(f"  [[{a}]] (core {core_a})  →  [[{c}]] (core {core_c})")
        print(f"    ratio {ratio:.0%}, {len(mediators)} mediator(s): {via}{suffix}")
        print()


# ── cliques ───────────────────────────────────────────────────────────────────

def cmd_cliques(graph: nx.DiGraph, min_size: int) -> None:
    """Find maximal cliques of size >= min_size in the undirected graph.

    A k-clique means k notes all linking to each other — a fully-connected
    subgraph. A tree over k notes needs k-1 edges; a k-clique has k*(k-1)/2.
    """
    undirected = graph.to_undirected()
    cliques = [c for c in nx.find_cliques(undirected) if len(c) >= min_size]
    cliques.sort(key=len, reverse=True)

    if not cliques:
        print(f"No maximal cliques of size {min_size}+ found.")
        return

    total_excess = sum(
        len(c) * (len(c) - 1) // 2 - (len(c) - 1)
        for c in cliques
    )
    print(f"Found {len(cliques)} maximal cliques of size {min_size}+")
    print(f"Excess edges over a tree across all cliques: ~{total_excess}\n")

    for i, clique in enumerate(cliques, 1):
        members = sorted(clique)
        tree_edges = len(clique) - 1
        actual_edges = len(clique) * (len(clique) - 1) // 2
        print(f"Clique {i} ({len(clique)} notes, {actual_edges} undirected edges, tree needs {tree_edges}):")
        for m in members:
            print(f"  [[{m}]]")
        print()


# ── reduction ─────────────────────────────────────────────────────────────────

def cmd_reduction(graph: nx.DiGraph) -> None:
    """Report edges made redundant by transitive reduction.

    Approach:
    1. Find strongly connected components (SCCs). Any SCC of size > 1 is a
       mutual-link cycle — all internal edges are redundant by transitivity.
    2. Condense the graph into a DAG of SCCs.
    3. Compute the transitive reduction of that DAG.
    4. Edges present in the condensation but absent from the reduction
       correspond to original edges reachable via longer inter-SCC paths.
    """
    # ── Step 1: mutual-link cycles (SCCs of size > 1) ──
    sccs = list(nx.strongly_connected_components(graph))
    cycles = sorted([s for s in sccs if len(s) > 1], key=len, reverse=True)

    if cycles:
        print(f"Found {len(cycles)} mutual-link cycle(s) (SCC size > 1):\n")
        for scc in cycles:
            members = sorted(scc)
            print(f"  {len(scc)}-cycle:")
            for m in members:
                print(f"    [[{m}]]")
            print()
    else:
        print("No mutual-link cycles found (graph is a DAG).\n")

    # ── Step 2: transitive reduction on condensed DAG ──
    condensation = nx.condensation(graph)
    tr = nx.transitive_reduction(condensation)

    removed_scc_edges = set(condensation.edges()) - set(tr.edges())

    if not removed_scc_edges:
        print("No inter-note edges removed by transitive reduction.")
        return

    # Map condensation edges back to original note pairs
    redundant_edges: list[tuple[str, str]] = []
    for u_scc, v_scc in removed_scc_edges:
        members_u: frozenset[str] = condensation.nodes[u_scc]["members"]
        members_v: frozenset[str] = condensation.nodes[v_scc]["members"]
        for a in members_u:
            for b in members_v:
                if graph.has_edge(a, b):
                    redundant_edges.append((a, b))

    redundant_edges.sort()
    print(f"Found {len(redundant_edges)} edges redundant by transitive reduction:\n")
    for a, b in redundant_edges:
        print(f"  [[{a}]]  →  [[{b}]]")


# ── bridge ────────────────────────────────────────────────────────────────────

def cmd_bridge(graph: nx.DiGraph, count: int, seed: int) -> None:
    """Sample cross-cluster note pairs with no current link."""
    rng = random.Random(seed)
    node_to_community = detect_communities(graph, seed)

    # Group nodes by community
    community_groups: dict[int, list[str]] = {}
    for node, cid in node_to_community.items():
        community_groups.setdefault(cid, []).append(node)
    communities = [g for g in community_groups.values() if len(g) >= 3]

    if len(communities) < 2:
        print("Not enough distinct communities found (need at least 2 with 3+ notes).")
        return

    print(f"Detected {len(communities)} communities ({len(node_to_community)} notes in largest component).")
    print(f"Showing {count} cross-cluster pairs with no existing link:\n")

    seen_pairs: set[tuple[str, str]] = set()
    found = 0
    attempts = 0

    while found < count and attempts < 500:
        attempts += 1
        c1, c2 = rng.sample(communities, 2)
        a = rng.choice(c1)
        b = rng.choice(c2)

        if graph.has_edge(a, b) or graph.has_edge(b, a):
            continue

        pair_key = (min(a, b), max(a, b))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        found += 1
        print(f"Pair {found}:")
        print(f"  [[{a}]]")
        print(f"  [[{b}]]")
        print()

    if found < count:
        print(f"(Only found {found} qualifying pairs after {attempts} attempts)")


# ── holes ─────────────────────────────────────────────────────────────────────

def cmd_holes(graph: nx.DiGraph, min_shared: int, cross_cluster: bool, seed: int) -> None:
    """Find pairs sharing min_shared+ common neighbors but no direct link.

    With --cross-cluster, restricts to pairs from different communities,
    which surfaces genuine bridge candidates rather than same-topic near-duplicates.
    """
    nodes = list(graph.nodes())

    # Undirected neighborhood per node (union of in- and out-edges)
    neighbors: dict[str, set[str]] = {
        n: (set(graph.successors(n)) | set(graph.predecessors(n)))
        for n in nodes
    }

    node_to_community: dict[str, int] = {}
    if cross_cluster:
        node_to_community = detect_communities(graph, seed)

    candidates: list[tuple[str, str, list[str]]] = []

    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if graph.has_edge(a, b) or graph.has_edge(b, a):
                continue
            if cross_cluster and node_to_community.get(a) == node_to_community.get(b):
                continue
            shared = sorted(neighbors[a] & neighbors[b])
            if len(shared) >= min_shared:
                candidates.append((a, b, shared))

    if not candidates:
        label = " cross-cluster" if cross_cluster else ""
        print(f"No{label} pairs found with {min_shared}+ shared neighbors.")
        return

    candidates.sort(key=lambda x: len(x[2]), reverse=True)

    cap = 50
    label = " cross-cluster" if cross_cluster else ""
    print(f"Found {len(candidates)}{label} pairs with {min_shared}+ shared neighbors (showing top {min(cap, len(candidates))}):\n")

    for a, b, shared in candidates[:cap]:
        shared_str = ", ".join(f"[[{s}]]" for s in shared[:4])
        if len(shared) > 4:
            shared_str += f" (+{len(shared) - 4} more)"
        print(f"  [[{a}]]")
        print(f"  [[{b}]]")
        print(f"    shared neighbors ({len(shared)}): {shared_str}")
        print()

    if len(candidates) > cap:
        print(f"  ... and {len(candidates) - cap} more pairs (raise --min-shared to filter)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serendipity tools for the wiki knowledge graph.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_tri = subparsers.add_parser("triangles", help="Find redundant A→C edges (sorted by redundancy ratio)")
    p_tri.add_argument("--min-mediators", type=int, default=1, help="Minimum alternative paths required (default: 1)")

    p_cliques = subparsers.add_parser("cliques", help="Find maximal cliques of size >= N (higher-order over-linking)")
    p_cliques.add_argument("--min-size", type=int, default=4, help="Minimum clique size (default: 4)")

    subparsers.add_parser("reduction", help="Transitive reduction: all edges covered by longer paths")

    p_bridge = subparsers.add_parser("bridge", help="Sample cross-cluster note pairs")
    p_bridge.add_argument("--count", type=int, default=10, help="Number of pairs to show (default: 10)")
    p_bridge.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")

    p_holes = subparsers.add_parser("holes", help="Find pairs sharing neighbors but no direct link")
    p_holes.add_argument("--min-shared", type=int, default=3, help="Minimum shared neighbors (default: 3)")
    p_holes.add_argument("--cross-cluster", action="store_true", help="Only show pairs from different communities")
    p_holes.add_argument("--seed", type=int, default=42, help="Random seed for community detection (default: 42)")

    args = parser.parse_args()

    print(f"Loading wiki graph from {WIKI_DIR}...")
    graph = load_graph()
    print(f"  {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    if args.command == "triangles":
        cmd_triangles(graph, min_mediators=args.min_mediators)
    if args.command == "cliques":
        cmd_cliques(graph, min_size=args.min_size)
    if args.command == "reduction":
        cmd_reduction(graph)
    if args.command == "bridge":
        cmd_bridge(graph, count=args.count, seed=args.seed)
    if args.command == "holes":
        cmd_holes(graph, min_shared=args.min_shared, cross_cluster=args.cross_cluster, seed=args.seed)


main()
