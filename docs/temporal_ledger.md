# Temporal Ledger

The temporal ledger records append-only events linked to Pulse Weaver
operations.  Each entry stores an `id`, timestamp, actor, action, reference,
proof identifier, and a SHA-256 hash of the canonical entry payload.

Entries are persisted to `state/temporal_ledger.jsonl`.  Helper renderers create
Markdown summaries, GraphViz DOT output, and lightweight SVG timelines.

## CLI

```
echo ledger snapshot --format md --out artifacts/
echo ledger tail --since "2025-01-01T00:00:00Z"
```

## API

- `GET /ledger/entries` – list entries with optional `since`/`limit`
- `GET /ledger/graph.svg` – render SVG timeline
