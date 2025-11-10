# Little Footsteps Bank Stack

This directory collects the artifacts required to bootstrap the Little Footsteps childcare commons bank:

- [`did.json`](./did.json) publishes the bank's `did:web` document (host on GitHub Pages at `/little-footsteps-bank/did.json`).
- [`trust_registry.json`](./trust_registry.json) enumerates recognized credential types and governance policies.
- [`first_credential.md`](./first_credential.md) documents the inaugural childcare voucher issuance.
- [`credentials/`](./credentials) stores example verifiable credential payloads for QA and demos.
- [`satoshi_vault_trust.md`](./satoshi_vault_trust.md) codifies the reserve relationship that backs the trust.

## Deployment checklist

1. Generate keys: `python scripts/generate_ed25519_keypair.py --out-dir state/little_footsteps/keys`.
2. Publish the DID document to `https://<your-gh-username>.github.io/little-footsteps-bank/did.json`.
3. Mirror `trust_registry.json` to the same GitHub Pages site for discoverability.
4. Start Postgres and run the issuer (`node apps/little_footsteps/vc_issuer/server.js`).
5. Deploy the Next.js dashboard from [`apps/little_footsteps/dashboard`](../../apps/little_footsteps/dashboard) to Vercel/Netlify for real-time observability.

Telemetry is emitted as structured JSON logs for ingestion into Prometheus, Grafana Loki, or any log aggregation pipeline.
