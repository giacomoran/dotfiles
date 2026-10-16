"""Report edges made redundant by transitive reduction.

Works in two steps:
1. Finds strongly connected components (SCCs) of size > 1 — mutual-link
   cycles where A→…→B and B→…→A both exist.
2. Condenses the graph into a DAG of SCCs, computes its transitive
   reduction, and maps removed edges back to original note pairs. These
   are edges reachable by a longer path and therefore never necessary.

This is the generalization of triangle detection: it catches redundancy
across paths of any length, not just length 2.

Usage:
    uv run python network-reduction.py
"""

import networkx as nx

from network_common import load_graph


def main() -> None:
    graph = load_graph()
    print(f"Loaded {graph.number_of_nodes()} notes, {graph.number_of_edges()} links\n")

    # ── Mutual-link cycles (SCCs of size > 1) ─────────────────────────────────
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
        print("No mutual-link cycles (graph is a DAG).\n")

    # ── Transitive reduction on condensed DAG ─────────────────────────────────
    condensation = nx.condensation(graph)
    tr = nx.transitive_reduction(condensation)
    removed_scc_edges = set(condensation.edges()) - set(tr.edges())

    if not removed_scc_edges:
        print("No inter-note edges removed by transitive reduction.")
        return

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


main()
