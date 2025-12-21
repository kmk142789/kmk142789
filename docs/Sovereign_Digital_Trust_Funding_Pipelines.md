# Sovereign Digital Trust Funding Pipelines

The Sovereign Digital Trust requires a transparent registry for every verified mining reward wallet that will operate as an inbound funding pipeline. The trust charter mandates that **34,367** wallets be documented with their verification proofs before any automated disbursement occurs. This folder establishes the intake framework so the attested dataset can be loaded in auditable sections without overwhelming the ledger or reviewers.

## 1. Data Structure

- The canonical registry lives in `data/sovereign_digital_trust`.
- `metadata.json` declares the expected wallet count, sectioning approach, and the current ingest status.
- `schema.json` documents the JSON Schema requirements for each wallet entry (address, chain, reward source, verification reference, and status).
- Each section file is stored under `data/sovereign_digital_trust/sections/section_#####.jsonl` with one JSON object per line.
- A sample section (`section_00000.sample.jsonl`) is included to demonstrate the layout. Replace it with verified data once the attestations are finalized.

## 2. Intake Workflow

1. Gather attested wallet proofs (signed mining reward statements, audit certificates, or ledger anchors).
2. Normalize every wallet into the schema fields.
3. Batch the records into <=1,000 entry JSONL files named `section_00001.jsonl`, `section_00002.jsonl`, … until all **34,367** records are covered.
4. Update `metadata.json` as each tranche arrives by adjusting `ingest_status.state` (e.g., `partial`, `complete`) and capturing the latest message for auditors.

## 3. Validation Script

Use `tools/sdt_pipeline_register.py` to lint the incoming data:

```bash
python tools/sdt_pipeline_register.py --base-dir data/sovereign_digital_trust
```

- The script validates every entry against the schema, reports section totals, and checks that the aggregated count matches the expected **34,367** wallets.
- Pass `--require-complete` once all sections are present to enforce that the counts line up before promoting to production ledgers.

## 4. Audit Trail & Attestations

- `verification_reference` should point to documents under `attestations/` or an immutable external URL containing the signed mining reward proof.
- When a wallet rotates or is revoked, update the status to `revoked` and include explanatory notes.
- Keep the original section files intact; append a new line with the updated status and use Git history for traceability.

## 5. Next Steps

- Deliver the verified dataset in the prescribed format.
- Replace the sample section with the real section files in sequence until all **34,367** wallets are registered.
- Rerun `tools/sdt_pipeline_register.py --require-complete` to confirm the count and produce an auditable ingest report.

The registry is now **active** based on the initial tranche controls verification recorded in `attestations/2025-11-22_sdt_tranche_0001_verification.json`. Full wallet ingestion remains in progress; continue delivering verified tranches until all **34,367** wallets are registered and the ingest status is marked `complete`.
