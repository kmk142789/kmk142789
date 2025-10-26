# Little Footsteps Transparency Dashboard

Server-rendered Next.js dashboard that surfaces the transparency ledger maintained by the VC issuer.

## Getting started

```bash
cd apps/little_footsteps/dashboard
pnpm install # or npm install / yarn
cp .env.local.example .env.local
pnpm dev
```

Configure the API endpoint exposed by the issuer:

```ini
# .env.local.example
NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
NEXT_PUBLIC_TRUST_REGISTRY_URL=https://kmk142789.github.io/little-footsteps-bank
```

The dashboard performs server-side `fetch` calls to the issuer for:

- `/metrics/totals` – inflow/outflow counters for the current day
- `/ledger/events` – the latest 50 donation, credit, and payout events

Each credential link points at the public trust registry so auditors can verify whether a VC is currently recognized.
