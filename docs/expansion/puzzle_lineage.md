# Puzzle Lineage

*Chapter I of the Echo Omni-Fusion Expansion*

The codex opened beneath a sky of luminescent hashes. Each puzzle, once a lone
star, now pulsed in constellation with its siblings. The Puzzle Constellation
Graph weaves this new cartography, extracting addresses from the historical
scrolls in `puzzle_solutions/` and binding them with traces of shared hash160
or echoed prefixes.

The lineage map exports three artifacts for every cycle:

- `build/constellation/constellation.json` — a structural ledger of nodes and
  edges for further analysis.
- `build/constellation/constellation.dot` — ready to visualize with Graphviz or
  any graph renderer.
- `build/constellation/constellation.png` — a quantum-stamped mosaic capturing
  node and edge counts for rapid diffing.

When a puzzle lacks siblings, the constellation still records its solitary
light, preserving the frontier for future explorers. The lineage chapter is
therefore living documentation: rerun `make constellation` and the star-map
reshapes itself.
