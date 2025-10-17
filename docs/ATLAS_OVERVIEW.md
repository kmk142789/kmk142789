# Echo Atlas Overview

Echo Atlas captures the persistent identity and network map for the Echo project.
It ingests repository documents, normalises ownership signals, and publishes an
SVG topology so the crew can reason about influence, assets, and interfaces.

## Quickstart

```bash
pip install -e .[dev]
export ATLAS_DATABASE_URL="sqlite:///data/atlas.db"
echocli atlas sync
open docs/ATLAS_REPORT.md
```

The sync command runs the importers, regenerates the Markdown report, and writes
`artifacts/atlas_graph.svg` for quick inspection.

## Architecture

```
+-----------------------+        +---------------------------+
|  Importers            |        |  Webhook (/hooks/atlas)   |
|  - CONTROL.md         |        |  Signature stub + queue   |
|  - SECURITY.md        |        +-------------+-------------+
|  - CODEOWNERS         |                      |
|  - docs/**            |                      v
+----------+------------+        +---------------------------+
           |                         Storage Adapter (SQLite)
           v                         - Nodes / Edges tables
   Atlas Repository                  - Change log
           |                         - Migrations metadata
           v
   Query & Visualiser
           |
    DOT + SVG + Reports
```

## Security Notes

- Webhook signatures must be at least eight characters and rotate quarterly.
- All importers operate on committed files—no secrets or runtime credentials are
  ingested.
- The default SQLite database lives in `data/atlas.db`. Override
  `ATLAS_DATABASE_URL` in a local `.env` file when deploying other adapters.
