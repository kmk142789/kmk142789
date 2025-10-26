# transparency.bank portal

This Next.js + Express bundle gives the public a real-time window into the Echo Bank sovereign treasury. The Express layer reads the sovereign ledger, compliance registry, proof bundles, and governance documents directly from the repository and exposes:

- `GET /api/status` — JSON snapshot of inflows, outflows, compliance credentials, governance amendments, audit trails, and proof bundles.
- `GET /api/stream` — Server-sent events stream that broadcasts live updates whenever ledger, compliance, or governance artifacts change.

The Next.js frontend consumes these endpoints to render the transparency dashboard, including JSON proof bundle listings and OpenTimestamps receipts.

## Running locally

```bash
cd apps/transparency.bank
npm install
npm run dev        # Next.js dev server at http://localhost:3030
```

To co-host the Express API and the Next.js frontend, run the custom server:

```bash
npm install
npm run api        # Starts Express + Next on http://localhost:3030
```

The server watches the following repository paths and pushes updates to the SSE clients:

- `ledger/little_footsteps_bank.jsonl`
- `legal/legal_posture_registry.jsonl`
- `proofs/little_footsteps_bank/`
- `puzzle_solutions/little_footsteps_bank.md`
- `GOVERNANCE.md`

These hooks ensure inflows, outflows, compliance proofs, governance amendments, and audit trails stay in sync with the sovereign ledger.
