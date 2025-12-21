# Voucher Governance Framework

## Purpose
Define the lifecycle, dispute process, and audit trail for voucher issuance, redemption, disputes, and resolution.

## Lifecycle
1. **Intake** — Voucher request logged in `state/vouchers/unresolved_queue.jsonl` with requester, purpose, and amount.
2. **Review** — Steward review assigns risk tier, required approvals, and SLA.
3. **Authorization** — Approved vouchers receive a unique ID and are recorded in issuance logs (future).
4. **Redemption** — Redeemed vouchers link to treasury or ledger entries with proof references.
5. **Closure** — Final state recorded in `state/vouchers/resolutions.jsonl` with outcomes and audit links.

## Dispute Process
1. **Dispute Filed** — Logged in `state/vouchers/disputes.jsonl` with reason, evidence, and requested remedy.
2. **Investigation** — Assigned reviewer gathers evidence and sets interim controls.
3. **Decision** — Resolution recorded in `state/vouchers/resolutions.jsonl` with findings and corrective actions.
4. **Appeal Window** — 14-day appeal period unless escalated by the Ombudsman.

## Required Fields (Queue)
- `voucher_id` (pending if intake only)
- `requester`
- `purpose`
- `amount`
- `currency`
- `submitted_at`
- `status`

## Required Fields (Disputes)
- `dispute_id`
- `voucher_id`
- `submitted_by`
- `submitted_at`
- `issue_summary`
- `status`
- `evidence`

## Required Fields (Resolutions)
- `resolution_id`
- `voucher_id`
- `decision`
- `decided_at`
- `actions`
- `evidence`

## Governance Owners
- **Primary:** Echo Treasury Authority
- **Oversight:** EOAG + Ombudsman
- **Ledger Mirror:** genesis_ledger/
