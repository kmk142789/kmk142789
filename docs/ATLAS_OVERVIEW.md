# Echo Atlas Overview

Echo Atlas tracks the persistent identity and network map for the Echo project.
It ingests canonical governance documents (CONTROL.md, SECURITY.md, CODEOWNERS)
and Markdown documentation to build a graph of people, bots, services, repos,
keys, and channels.

## Quickstart

```bash
pip install -e .[dev]
echocli atlas sync
```

This command runs the importers, applies migrations, emits a Markdown report at
`docs/ATLAS_REPORT.md`, and renders `artifacts/atlas_graph.svg` so you can share
an at-a-glance view of ownership and dependencies.

## Architecture

```
+------------------+       +-------------------+
|  Importers       |       |  Webhooks         |
|  CONTROL.md      |       |  POST /atlas/hooks|
|  SECURITY.md     |       +-------------------+
|  CODEOWNERS      |                 |
|  docs/**/*.md    |                 v
+--------+---------+       +-------------------+
         |                 |  Atlas Service    |
         v                 |  (sync + reports) |
+------------------+       +-------------------+
|  SQLite Adapter  |<----->|  Atlas Repository |
+------------------+       +-------------------+
         |
         v
+------------------+
|  Reports & SVG   |
+------------------+
```

## Security Notes

- Webhook payloads must be signed and rotated regularly.
- All data written to `docs/ATLAS_REPORT.md` and `artifacts/atlas_graph.svg` is
  derived from repository sources; never store secrets in the atlas database.
- The default adapter uses SQLite at `data/atlas.db`. Swap in a custom adapter to
  target Postgres or another backend once credentials are available.

## Extensibility

- Importers follow a simple interface so you can add new sources without
  touching storage.
- The `AtlasService` exposes `list_nodes`, `list_edges`, and `build_summary`
  helpers for dashboards and automation hooks.

## Harmonix search filters

Use the dedupe job to emit a `federated_search_index/index.json` file. With the
index in place you can combine text queries with Harmonix metadata filters to
locate specific cycles, puzzles, or signing addresses:

```bash
python -m atlas.search \
  --index path/to/federated_search_index \
  --query "harmonix" \
  --cycle 7 \
  --puzzle 256 \
  --address bc1qexampleaddress
```

The `atlas atlas_cli.py search` subcommand exposes the same `--cycle`,
`--puzzle`, and `--address` arguments if you prefer the multiplexer entry
point.
