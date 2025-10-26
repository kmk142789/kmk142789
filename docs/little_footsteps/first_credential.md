# Little Footsteps – First Credential Issuance

The first credential produced by the Little Footsteps issuer demonstrates the “seamless licensing” milestone. It uses the Ed25519 key material generated via `scripts/generate_ed25519_keypair.py` on 2025-05-11 and is anchored to the public DID document published at `docs/little_footsteps/did.json` (mirrored to GitHub Pages).

## Credential snapshot

- **Type:** `LittleFootstepsChildcareVoucher`
- **Subject:** Amelia Rivera (caregiver DID `did:key:z6MkuVgbdemoParent`)
- **Value:** 40 subsidized childcare hours (USD 600 equivalent)
- **Ledger entry:** Logged as an `OUTFLOW` of 60000 cents with tag `voucher-issuance`
- **Proof:** Ed25519Signature2020 using verification method `did:web:kmk142789.github.io:little-footsteps-bank#ed25519-2024`

The full payload and proof artifact are preserved at [`docs/little_footsteps/credentials/little_footsteps_childcare_voucher.json`](./credentials/little_footsteps_childcare_voucher.json).

## Transparency ledger record

| Field | Value |
| ----- | ----- |
| `direction` | `OUTFLOW` |
| `amount_cents` | `60000` |
| `currency` | `USD` |
| `beneficiary` | `did:key:z6MkuVgbdemoParent` |
| `tags` | `["voucher-issuance", "pilot"]` |
| `vc_id` | `vc:childcare:demo-001` |
| `occurred_at` | `2025-05-11T00:01:12Z` |

The dashboard pulls this event through the `/ledger/events` endpoint to keep donors and regulators aligned on every payout.

## Reproduction steps

1. Ensure Postgres is running and the issuer service has `DATABASE_URL`, `VC_ISSUER_DID`, and `VC_PRIVATE_KEY_PATH` configured (see [`apps/little_footsteps/vc_issuer/.env.example`](../../apps/little_footsteps/vc_issuer/.env.example)).
2. Start the issuer: `node apps/little_footsteps/vc_issuer/server.js`.
3. POST the following payload to `http://localhost:4000/issue/childcare-voucher`:

```json
{
  "credentialSubject": {
    "id": "did:key:z6MkuVgbdemoParent",
    "familyName": "Rivera",
    "givenName": "Amelia",
    "householdSize": 3
  },
  "ledgerEvent": {
    "direction": "OUTFLOW",
    "amount_cents": 60000,
    "currency": "USD",
    "beneficiary": "did:key:z6MkuVgbdemoParent",
    "tags": ["voucher-issuance", "pilot"],
    "purpose": "Pilot childcare voucher distribution"
  }
}
```

4. The issuer responds with the VC and a pointer to the ledger entry, while console logs emit JSON telemetry for Prometheus/Grafana ingestion.

This closes the bootstrap loop: ledger connectivity, DID anchoring, verifiable credential issuance, and operational telemetry all run end-to-end.
