"""Find edges A→C that are redundant because A→B→C already exists.

Sorted by redundancy ratio (mediators / out-degree of A), so a node with
most of its out-edges covered ranks higher than a large hub with a few
incidentally covered edges. K-core number is shown per endpoint: high-core
notes are deep inside dense clusters and are the most important to fix.

Usage:
    uv run python network-triangles.py [--min-mediators N]
"""

import argparse

import networkx as nx

from network_common import load_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-mediators", type=int, default=1, help="Minimum alternative paths required (default: 1)")
    args = parser.parse_args()

    graph = load_graph()
    print(f"Loaded {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    core_number = nx.core_number(graph.to_undirected())

    redundant: list[tuple[str, str, list[str], float]] = []
    for a, c in graph.edges():
        mediators = [b for b in graph.successors(a) if b != c and graph.has_edge(b, c)]
        if len(mediators) < args.min_mediators:
            continue
        out_degree = graph.out_degree(a)
        ratio = len(mediators) / out_degree if out_degree > 0 else 0.0
        redundant.append((a, c, mediators, ratio))

    if not redundant:
        print(f"No redundant edges found with {args.min_mediators}+ mediators.")
        return

    redundant.sort(key=lambda x: x[3], reverse=True)

    print(f"Found {len(redundant)} edges with {args.min_mediators}+ mediators (sorted by redundancy ratio):\n")
    for a, c, mediators, ratio in redundant:
        core_a = core_number.get(a, 0)
        core_c = core_number.get(c, 0)
        via = ", ".join(f"[[{b}]]" for b in mediators[:3])
        suffix = f" (+{len(mediators) - 3} more)" if len(mediators) > 3 else ""
        print(f"  [[{a}]] (core {core_a})  →  [[{c}]] (core {core_c})")
        print(f"    ratio {ratio:.0%}, {len(mediators)} mediator(s): {via}{suffix}")
        print()


main()
