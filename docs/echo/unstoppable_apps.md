# Unstoppable Apps

The Echo Bridge keeps Unstoppable Domains in sync with every pulse cycle so external
portals and wallets can reference the latest mythogenic state without guessing. The
`UnstoppableDomainConnector` gathers domains from PulseNet registrations, merges them
with optional defaults, and stages a metadata update describing the active cycle,
coherence, and canonical manifest path for each record.【F:packages/core/src/echo/bridge/service.py†L94-L135】

## Registering domains

PulseNet registrations accept an `unstoppable_domains` field alongside ENS, wallet,
and Vercel data. Incoming payloads are normalised into lists of strings before being
persisted, which ensures a connector run always receives clean domain values.【F:packages/core/src/echo/pulsenet/models.py†L12-L77】
When the resolver processes a query it folds those values together with any optional
static hints supplied in `state/pulsenet/resolver_sources.json`, providing aggregated
results across Unstoppable, ENS, Vercel, and wallet buckets.【F:packages/core/src/echo/pulsenet/resolver.py†L92-L131】【F:pulsenet-gateway.md†L1-L54】

Typical flow:

1. `POST /pulsenet/register` with contact info plus the desired Unstoppable names.
2. Optionally add shared defaults (for example, `josh.echo.crypto`) to
   `state/pulsenet/resolver_sources.json` if they should appear for every lookup.
3. Trigger a bridge cycle so the connector prepares an Unstoppable metadata event and
   hands it to whichever automation updates the DNS records.【F:packages/core/src/echo/bridge/service.py†L337-L359】

## Resolving records

PulseNet’s `/pulsenet/resolve` endpoint now exposes the merged namespace, letting
clients confirm which Unstoppable entries are attached to a registrant without leaving
Echo.【F:pulsenet-gateway.md†L17-L31】 For ad-hoc checks or troubleshooting you can use the
`tools/unstoppable_resolver.js` helper to query the official resolution API. The script
supports specifying the token ticker, optional chain (such as `ERC20`), writing results
to JSON, and overriding RPC endpoints or API keys via environment variables.【F:tools/unstoppable_resolver.js†L1-L109】

Example:

```bash
node tools/unstoppable_resolver.js echo.crypto --ticker ETH --json echo.json
```

## Operational defaults

Bridge deployments that set `ECHO_BRIDGE_UNSTOPPABLE_DOMAINS` will publish those domains
alongside whatever the registrations supplied, guaranteeing a baseline set of records
even if no new entries were submitted in the current cycle.【F:packages/core/src/echo/bridge/service.py†L337-L359】 The
resulting `SyncEvent` payload is ready for downstream automation or manual updates,
ending the "under construction" placeholder and giving Unstoppable apps live data the
moment a cycle completes.【F:packages/core/src/echo/bridge/service.py†L120-L135】
