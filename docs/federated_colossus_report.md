# Federated Colossus Reporting

The federated Colossus report stitches together the merged Atlas
federation graph, the deduplicated search index, Harmonix payload
snapshots, and the COLOSSUS cycle directory structure.  The
`atlas.reporting.generate_federated_colossus_report` helper produces a
Markdown narrative (`federated_colossus_index.md`) alongside a
structured JSON artifact (`federated_colossus_index.json`).

## Inputs

* `graph_path` – the merged federation graph produced by
  `atlas.federation.build_global_graph`.
* `search_index_path` – directory or file containing `index.json`
  emitted by `atlas.dedupe`.
* `colossus_root` – the COLOSSUS cycle directory (`cycle_00001`, …)
  holding datasets, lineage maps, and glyph narratives.
* `puzzle_root` – directory of reconstructed puzzle solutions used to
  derive addresses.
* `harmonix_sources` – optional iterable of Harmonix payload JSON files
  (defaulting to `*.echo.json` in the current working directory).

## Outputs

* **Cycle overview** – sorted by cycle number, merging glyph signatures
  with Harmonix mythocode summaries and any matching search-index hits.
* **Puzzle mapping** – table describing each reconstructed puzzle and
  its derived address hash.
* **Derived address catalog** – deduplicated list of addresses with the
  puzzles that produced them.

The JSON artifact mirrors this structure to make integration with
dashboards or data tooling straightforward.  Because the renderer
normalises, deduplicates, and sorts every section, incremental updates
only append new cycles or puzzles without rearranging previous entries.

