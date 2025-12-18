# Governance Engine Harness

The governance harness coordinates proposals, records decisions, and appends evolution logs into the canonical ledgers. Each entry is written to `genesis_ledger/ledger.jsonl` and mirrored into future ledger files when they are rolled forward.

## Flow
1. **Proposal Intake** – Proposals are submitted with author, scope, and narrative. They are queued and stamped with the next sequence number.
2. **Decision Cycle** – Guardians or automated policy checks update the proposal with decision metadata (approved, deferred, rejected) plus signatures.
3. **Evolution Log** – Implementation notes and follow-up tasks are appended as evolution logs that reference the governing proposal sequence.
4. **Ledger Write** – Each state change emits a JSON line into `genesis_ledger/ledger.jsonl` and any active continuation ledgers. Every entry includes timestamps, digests, and linkage to prior decisions.

## Ledger Entry Shape
```json
{
  "seq": 1024,
  "timestamp": "2024-01-01T12:00:00Z",
  "kind": "decision",
  "proposal_id": "GOV-2024-001",
  "narrative": "Approved NGO dashboard publication",
  "actors": ["guardian:prime", "governance-engine"],
  "digest": "sha256:...",
  "links": {"proposal": 1023, "previous": 1022}
}
```

## Forward Compatibility
- When a new ledger (e.g., `ledger_v2.jsonl`) is initiated, the harness mirrors writes to both the genesis ledger and the new file until cut-over is complete.
- Evolution logs track when ledgers rotate, including the reason, target filename, and migration digest.

## Operational Notes
- Always write one JSON object per line.
- Preserve ordering—sequence numbers must be monotonic across ledgers.
- Include digests to enable downstream proof-pack generation via the bridge protocol.
