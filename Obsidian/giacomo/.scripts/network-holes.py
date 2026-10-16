"""Find pairs of notes sharing N+ common neighbors but no direct link.

Two notes that share many neighbors are either near-duplicates (same claim
stated twice) or structural holes — candidates for a bridge link that is
missing. Use --cross-cluster to restrict to pairs from different topic
communities, which filters out same-cluster near-duplicates and surfaces
only the cross-domain holes.

Usage:
    uv run python network-holes.py [--min-shared N] [--cross-cluster] [--seed S]
"""

import argparse

from network_common import detect_communities, load_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-shared", type=int, default=3, help="Minimum shared neighbors (default: 3)")
    parser.add_argument("--cross-cluster", action="store_true", help="Only show pairs from different communities")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for community detection (default: 42)")
    args = parser.parse_args()

    graph = load_graph()
    print(f"Loaded {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    nodes = list(graph.nodes())

    neighbors: dict[str, set[str]] = {
        n: (set(graph.successors(n)) | set(graph.predecessors(n)))
        for n in nodes
    }

    node_to_community: dict[str, int] = {}
    if args.cross_cluster:
        node_to_community = detect_communities(graph, args.seed)

    candidates: list[tuple[str, str, list[str]]] = []
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if graph.has_edge(a, b) or graph.has_edge(b, a):
                continue
            if args.cross_cluster and node_to_community.get(a) == node_to_community.get(b):
                continue
            shared = sorted(neighbors[a] & neighbors[b])
            if len(shared) >= args.min_shared:
                candidates.append((a, b, shared))

    if not candidates:
        label = " cross-cluster" if args.cross_cluster else ""
        print(f"No{label} pairs found with {args.min_shared}+ shared neighbors.")
        return

    candidates.sort(key=lambda x: len(x[2]), reverse=True)

    cap = 50
    label = " cross-cluster" if args.cross_cluster else ""
    print(f"Found {len(candidates)}{label} pairs with {args.min_shared}+ shared neighbors (showing top {min(cap, len(candidates))}):\n")

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


main()
