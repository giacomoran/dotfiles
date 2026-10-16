"""Find maximal cliques of size >= N in the undirected wiki link graph.

A k-clique means k notes all linking to each other — a fully-connected
subgraph. A tree over k notes needs k-1 edges; a k-clique has k*(k-1)/2,
so a 6-clique carries 10 excess edges. These are the highest-ROI targets
for restructuring toward clean hierarchies.

Usage:
    uv run python network-cliques.py [--min-size N]
"""

import argparse

import networkx as nx

from network_common import load_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-size", type=int, default=4, help="Minimum clique size (default: 4)")
    args = parser.parse_args()

    graph = load_graph()
    print(f"Loaded {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    undirected = graph.to_undirected()
    cliques = [c for c in nx.find_cliques(undirected) if len(c) >= args.min_size]
    cliques.sort(key=len, reverse=True)

    if not cliques:
        print(f"No maximal cliques of size {args.min_size}+ found.")
        return

    total_excess = sum(len(c) * (len(c) - 1) // 2 - (len(c) - 1) for c in cliques)
    print(f"Found {len(cliques)} maximal cliques of size {args.min_size}+")
    print(f"Excess edges over a tree across all cliques: ~{total_excess}\n")

    for i, clique in enumerate(cliques, 1):
        members = sorted(clique)
        tree_edges = len(clique) - 1
        actual_edges = len(clique) * (len(clique) - 1) // 2
        print(f"Clique {i} ({len(clique)} notes, {actual_edges} undirected edges, tree needs {tree_edges}):")
        for m in members:
            print(f"  [[{m}]]")
        print()


main()
