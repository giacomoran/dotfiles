"""Shared graph loading and community detection for network-*.py tools."""

import random
import re
from pathlib import Path

import networkx as nx

VAULT_PATH = Path(__file__).parent.parent
WIKI_DIR = VAULT_PATH / "👾 Wiki"

EXCLUDE_NAMES = {"Index.md", "Log.md", "CLAUDE.md"}

# Matches [[Note Title]], [[Note Title#section]], [[Note Title|alias]]
LINK_PATTERN = re.compile(r'\[\[([^\]|#\n]+?)(?:[#|][^\]\n]*)?\]\]')


def load_graph() -> nx.DiGraph:
    """Parse all wiki notes and build a directed link graph."""
    graph = nx.DiGraph()

    notes: dict[str, Path] = {}
    for path in WIKI_DIR.glob("*.md"):
        if path.name in EXCLUDE_NAMES:
            continue
        title = path.stem
        notes[title] = path
        graph.add_node(title)

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
