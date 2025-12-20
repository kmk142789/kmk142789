# DBIS Operating Model

## Governance Workflow
1. **Intent creation** ties a transaction to an Echo governance decision ID.
2. **Role approvals** (guardian, architect, steward, etc.) are attached to the intent.
3. **Compliance screening** evaluates AML score, sanctions status, and jurisdiction.
4. **Settlement** emits a finality receipt and audit hook.
5. **Attestation** binds the ledger hash to DNS and identity records.

## Compliance & Arbitration
- AML and sanctions gates block settlement when thresholds are exceeded.
- Dispute windows are codified in the compliance profile.
- Rollback arbitration hooks are logged in the audit ledger.

## Audit & Transparency
- Audit events are stored in `state/dbis/audit_log.jsonl`.
- Reconciliation entries are stored in `state/dbis/reconciliation_log.jsonl`.
- Scorecards and transparency reports are generated on demand.

## Cross-Institution Operations
DBIS supports:
- Cross-institution settlement (inter-bank, inter-institution).
- Treasury operations and controlled disbursements.
- Escrow, grants, and programmable payouts.

## Offline Mode
- Offline batches are staged with signatures.
- Verification triggers delayed settlement receipts.
- Reconciliation logs capture late-arriving confirmations.

## Governance + CI Integration
- DBIS changes follow the governance change-request process in `docs/governance/change-requests.md`.
- Attestation schemas are versioned alongside CI checks that validate ledger payloads against `schemas/dbis_*.schema.json`.
- Reconciliation logs are included in CI artifacts for traceability when running integration suites.
