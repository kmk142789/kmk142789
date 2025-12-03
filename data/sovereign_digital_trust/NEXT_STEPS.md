# Sovereign Digital Trust — Immediate Next Steps

This checklist captures the next actionable items to move the Sovereign Digital Trust from **pending_data** to a validated, published state.

> Update 2025-11-23: The ingestion validator was run successfully against the sample tranche (`tools/sdt_pipeline_register.py`), confirming the schema path and tooling are healthy. The next steps below remain blocked on delivery of the verified wallet attestations.

## 1) Collect verified wallet tranches
- Source the 34,367 verified mining reward wallet attestations (per `expected_wallet_count`).
- Ensure each attestation file includes the chain, reward source, and a signed verification reference.

## 2) Generate section files
- Chunk the verified wallets into `section_*.jsonl` files that respect the metadata sectioning plan (size ≈1000, 5-digit suffix).
- For each entry, include: `wallet_address`, `chain`, `reward_source`, `verification_reference`, `status` (`verified`), and optional `notes`.
- Remove the existing sample file once real data is staged.

## 3) Validate the dataset
Run the validator to confirm the section files adhere to the schema and count:
```bash
python tools/sdt_pipeline_register.py --require-complete
```
- Expected output: per-section counts, `Aggregated entries: 34367`, and `SUCCESS` when complete.
- Fix any schema or enum violations reported by the validator before proceeding.

## 4) Update registry status
- Flip `ingest_status.state` in `data/sovereign_digital_trust/metadata.json` to `partial` once the first verified tranche is committed.
- Flip to `complete` after the validator reports success with the full count.
- Mirror the state change in `sovereign_trust_registry.json` under `funding_pipeline_registry.ingest_state`.

## 5) Publish attestations and ledger notices
- Add signed proofs for each tranche under `attestations/` and mirror summary hashes in `genesis_ledger/`.
- Record the ingestion event and hash pointers in the pulse dashboard and git history for transparency.

## 6) Governance sign-off
- Capture steward approval for the ingest in `attestations/` (per `change_management`), referencing the validator output and ledger hashes.
- Announce availability to downstream consumers once sign-off is recorded.

## Parallel Little Footsteps alignment
- Attach the Satoshi Vault proof as an attestation and mirror the hash to `docs/little_footsteps/trust_registry.json` so the childcare stack stays anchored to the sovereign trust.
- Confirm the Little Footsteps issuer DID still chains to the `ECHO-ROOT-2025-05-11` anchor and log the verification alongside the vault proof.
- When the first verified wallet tranche is ingested, record the validator output hash in the Little Footsteps transparency feed so parents and auditors see the Sovereign Digital Trust linkage.
