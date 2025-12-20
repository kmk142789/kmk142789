# DBIS Architecture

## Core Components
1. **Transaction Engine** (`src/dbis/engine.py`)
   - Validates intents against identity, DNS, and compliance signals.
   - Produces settlement receipts with finality hashes.
   - Emits audit events and reconciliation entries.

2. **Monetization Layer** (`src/dbis/monetization.py`)
   - Grants, subscriptions, royalties, and escrow releases.
   - Institutional wallet controls and role-based approvals.

3. **Stress Testing** (`src/dbis/simulation.py`)
   - Scenario-driven validation checks.
   - Failure-rate thresholds for systemic risk analysis.

4. **Attestation Schemas** (`schemas/dbis_*.schema.json`)
   - DBIS transaction, attestation, and audit event schemas.

## Integrity & Finality
- Every ledger entry is hash-chained.
- Settlement receipts bind the intent, compliance snapshot, and ledger hash.
- Audit hooks point to dispute resolution and rollback arbitration workflows.

## Compliance-by-Construction
- AML risk limits enforced at validation.
- Sanctions status must be `clear` before settlement.
- Governance references are mandatory for all intents.
- Dispute windows and rollback policy are captured in compliance profiles.

## Identity + DNS Binding
- Party identities require `identity_id`, `did`, and `dns_record`.
- Attestation records bind intents to DNS substrate entries.
- DNS provenance follows `docs/dns/echo_dns_root_substrate.md`.

## Multi-Rail Support
DBIS accepts intents across:
- Fiat rails
- CBDC rails
- Stablecoin rails
- Tokenized assets
- Off-chain instruments

## Offline Continuity
- Offline batches are staged, signed, and verified on reconnect.
- Delayed settlement receipts capture verification metadata.
