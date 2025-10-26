# Little Footsteps Transparency Bank Launch Plan

This document distills the "bank licenses itself" concept into an actionable implementation roadmap. It captures the two-track launch approach, identity and credentialing stack, core data schema, transparency dashboard requirements, compliance guardrails, and operational automations that can be executed immediately.

## 1. Launch Strategy Overview

### Track A — Fast Path (48–72 hour MVP)
- **Objective:** begin accepting donations, execute transparent payouts, and publish a live ledger while formal paperwork progresses.
- **Entity Wrapper:**
  - Use an existing nonprofit if available; otherwise engage a fiscal sponsor to accept tax-deductible donations on day one.
- **Financial Rails:**
  - Stripe nonprofit account for card/ACH donations.
  - Dedicated business checking account for payouts.
  - Postgres (preferred) or Google Sheets as the canonical transparency ledger until the full stack is deployed.
- **Transparency Outputs:**
  - Public Next.js dashboard that streams inflows/outflows in near real time.
  - DonationReceipt and ImpactPayout verifiable credentials (VCs) minted for donors and vendors.

### Track B — Formal Path (4–12 weeks, parallel)
- Incorporate or partner for a 501(c)(3) entity; maintain the fiscal sponsor relationship until IRS determination is complete.
- Form a wholly controlled LLC subsidiary for low-risk yield activities if desired.
- Pursue credit union/CDFI partnerships for banking rails instead of a full charter; your software becomes the transparency, credential, and payout layer on top.
- Combine symbolic trust (VC-based registry) with formal compliance filings to reinforce credibility.

### Mini-Checklist (Sunday, Oct 26, 2025 — America/Detroit)
- [ ] Confirm fiscal sponsor or existing 501(c)(3).
- [ ] Create repositories: `lfs-ledger-core`, `lfs-vc-issuer`, `lfs-dashboard`, `lfs-trust-registry`, `lfs-ops`.
- [ ] Commit schema and VC JSON artifacts.
- [ ] Publish `did.json` via GitHub Pages for the issuer.
- [ ] Connect `/payouts/create` to VC issuance and dashboard.
- [ ] Seed 10 inflows + 6 outflows, validate dashboard rendering.

## 2. Identity & Credential Layer

### Decentralized Identifiers
- Start with `did:web` hosted on `https://yourdomain/.well-known/did.json` (template provided in `templates/little_footsteps/did_web.json`).
- Add additional DID methods (`did:ion`, `did:key`) as the trust graph expands.

### Credential Types
1. **DonationReceiptCredential** — proof a donation hit the ledger.
2. **ImpactPayoutCredential** — proof that funds were disbursed to an impact vendor/expense.
3. **ProviderCredential** — attestation that the daycare/site/vendor is verified.

Each credential is signed with an Ed25519 key referenced in the DID document. Issue credentials via OpenID4VCI-compatible endpoints as the issuer service matures.

## 3. Data & Ledger Architecture

### Postgres Schema
Embed the following SQL migration in `lfs-ledger-core`:

```sql
-- donors, inflows, outflows, vc proofs
CREATE TABLE donors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  did TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE inflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT,
  amount_cents INT NOT NULL,
  currency TEXT DEFAULT 'USD',
  donor_id UUID REFERENCES donors(id),
  ext_tx_id TEXT,
  received_at TIMESTAMPTZ DEFAULT now(),
  vc_id TEXT,
  metadata JSONB DEFAULT '{}'
);

CREATE TABLE outflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  purpose TEXT,
  beneficiary TEXT,
  vendor TEXT,
  amount_cents INT NOT NULL,
  currency TEXT DEFAULT 'USD',
  paid_at TIMESTAMPTZ DEFAULT now(),
  supporting_docs JSONB,
  vc_id TEXT,
  metadata JSONB DEFAULT '{}'
);

CREATE TABLE ledger_events (
  id BIGSERIAL PRIMARY KEY,
  direction TEXT CHECK (direction IN ('INFLOW','OUTFLOW')),
  ref_id UUID NOT NULL,
  occurred_at TIMESTAMPTZ DEFAULT now(),
  snapshot JSONB
);
```

### Public JSON Log Example

```json
{
  "event": "INFLOW",
  "occurred_at": "2025-10-26T14:21:10Z",
  "inflow": {
    "source": "stripe",
    "amount": 10000,
    "currency": "USD",
    "donor_did": "did:key:zDonor",
    "ext_tx_id": "pi_3N123...",
    "vc_id": "vc:donation:0x5a2c...e1",
    "note": "General fund"
  }
}
```

## 4. Application Stack Deliverables

### `lfs-ledger-core`
- REST API with Stripe webhook ingestion (`/webhooks/stripe`).
- `/payouts/create` endpoint to write `outflows`, attach documentation, invoke VC minting, and record `ledger_events`.
- Seed script generating demo inflows/outflows and associated VC references.
- JSON export endpoint for public dashboards.

### `lfs-vc-issuer`
- Node.js (Express) or Go service.
- Hosts DID document (GitHub Pages or static site).
- Generates and stores Ed25519 keys (rotate quarterly; retain old keys in DID doc).
- Endpoints: `/issue/donation-receipt`, `/issue/impact-payout`, `/verify`.
- Persists credential hashes and returns `vc_id` for ledger linkage.

### `lfs-dashboard`
- Next.js app with server-side rendering for latest 50 ledger events.
- Visualizes daily totals, inflow/outflow breakdown, and tag filters (meals, supplies, rent, etc.).
- Provides "Follow your dollar" traceability from donor receipts to associated outflows.
- Honors donor privacy toggles (show as "Anonymous" if desired).

### `lfs-trust-registry`
- Static JSON registry enumerating issuer DID, credential types, and policy URIs.
- Signed payload stored in version control; publish signature verification instructions.

### `lfs-ops`
- Operational playbooks (POLICY.md): donor privacy, restricted fund handling, payout verification, W-9 collection, 1099 issuance, incident response.

## 5. Compliance & Risk Controls

- **Donor receipts:** Issue DonationReceipt VC plus traditional acknowledgment letters (especially when using a fiscal sponsor).
- **Vendor payouts:** Collect W-9s; emit 1099-NEC where applicable.
- **AML/KYC:** Maintain vendor verification data; escalate large/atypical donations to the fiscal sponsor for review.
- **Privacy:** Publish hashed identifiers for donors in the public log; keep PII internal.
- **Security:** Rotate signing keys quarterly; maintain previous keys in DID document for verification continuity.

## 6. Operational Automations

1. Tag every inflow by fund/restriction.
2. Allocate unrestricted funds to core operations first, then programmatic spend.
3. For each outflow:
   - Attach supporting documents (links, IPFS hashes).
   - Mint ImpactPayout VC.
   - Surface the transaction on the dashboard within five minutes.

## 7. Trust Registry Blueprint

Publish a signed JSON document similar to the following:

```json
{
  "id": "did:web:yourdomain#trust-registry",
  "issuer": "did:web:yourdomain",
  "registryVersion": "1.0.0",
  "credentialTypes": [
    "DonationReceiptCredential",
    "ImpactPayoutCredential",
    "ProviderCredential"
  ],
  "policyUris": [
    "https://yourdomain/policies/donor-privacy",
    "https://yourdomain/policies/impact-verification"
  ],
  "proof": { "...": "signature by your DID key" }
}
```

## 8. Additional Assets

- `.env` template with required secrets, keys, and connection strings (see `plans/little_footsteps/env.example`).
- Ed25519 key generation script (`scripts/generate_ed25519_keypair.py`).
- Minimal Express-based VC issuer server scaffold (`templates/little_footsteps/vc_issuer_server.js`).
- Next.js dashboard page scaffold for ledger visualization (`templates/little_footsteps/dashboard_page.tsx`).

Leverage these assets to bootstrap repositories quickly and keep them synchronized via automation (e.g., GitHub Actions for lint/test/migrate/build). Update the ledger log, changelog, and VC samples on every deployment cycle.
