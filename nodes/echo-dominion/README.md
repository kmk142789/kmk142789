# Echo Dominion Node

This node exposes the Echo Dominion NGO dashboard and a minimal set of endpoints used by the bridge protocol.

## Endpoints
- `GET /health` — health probe for orchestration and uptime checks.
- `GET /ngo/endpoints` — returns the list of NGO endpoints and their purposes.
- `GET /ngo/dashboard` — lightweight dashboard response for status, bridge bindings, and ledger preview.
- `GET /ngo/ledger` — previews the latest entries from `genesis_ledger/ledger.jsonl` when available.

## Running

```bash
npm install
npm start
```

Set `PORT` to override the default `4040` listener.
