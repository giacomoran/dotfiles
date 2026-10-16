"""Sample cross-cluster note pairs with no current link for serendipity review.

Detects communities via label propagation, then draws one note from each of
two different communities. Pairs that already share a link are skipped. The
intent is to surface notes that are topically distant from each other —
candidates for a genuinely novel cross-domain connection or contradiction.

Re-run with different --seed values to get a fresh sample each time.

Usage:
    uv run python network-bridge.py [--count N] [--seed S]
"""

import argparse
import random

from network_common import detect_communities, load_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=10, help="Number of pairs to show (default: 10)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    graph = load_graph()
    print(f"Loaded {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    rng = random.Random(args.seed)
    node_to_community = detect_communities(graph, args.seed)

    community_groups: dict[int, list[str]] = {}
    for node, cid in node_to_community.items():
        community_groups.setdefault(cid, []).append(node)
    communities = [g for g in community_groups.values() if len(g) >= 3]

    if len(communities) < 2:
        print("Not enough distinct communities (need at least 2 with 3+ notes).")
        return

    print(f"Detected {len(communities)} communities ({len(node_to_community)} notes in largest component).")
    print(f"Showing {args.count} cross-cluster pairs with no existing link:\n")

    seen_pairs: set[tuple[str, str]] = set()
    found = 0
    attempts = 0

    while found < args.count and attempts < 500:
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

    if found < args.count:
        print(f"(Only found {found} qualifying pairs after {attempts} attempts)")


main()
