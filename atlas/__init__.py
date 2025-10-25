"""Atlas federation toolkit."""

from .graph import ArtifactNode, Edge, FederationGraph
from .federation import build_global_graph
from .dedupe import build_dedupe_index
from .resolver import merge_universes

__all__ = [
    "ArtifactNode",
    "Edge",
    "FederationGraph",
    "build_global_graph",
    "build_dedupe_index",
    "merge_universes",
]
