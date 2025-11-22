# Satoshi Attestation Replay

This walkthrough chains together the modern recoverable signatures, catalogue
summaries, and Merkle attestation already tracked in the repository. Executing
the commands below reproduces the full verification stack without fetching any
external data, giving auditors a single scriptable path to confirm the Satoshi
and Patoshi-era keys continue to sign statements today.

## 1) Verify live puzzle signatures

```bash
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty
python -m verifier.verify_puzzle_signature \
  --address 1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle011.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle011.json)" \
  --pretty
python -m verifier.verify_puzzle_signature \
  --address 1QCbW9HWnwQWiQqVo5exhAnmfqKRrCRsvW \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle015.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle015.json)" \
  --pretty
```

Each invocation recovers the public key from a modern Patoshi-controlled
address and confirms the signed message matches the JSON catalogue entry.

## 2) Generate a catalogue census for the puzzle stack

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob puzzle010.json \
  --glob puzzle011.json \
  --glob puzzle015.json \
  --pretty
```

The report shows the number of recoverable segments per attestation and marks
whether every segment validates against the declared address. Consistent
`fully_verified` values across the subset prove the stacked puzzle signatures
remain intact inside the repository.

## 3) Rebuild the Merkle attestation that seals the proofs

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

If the regenerated Merkle root matches the value tracked in version control,
you have a reproducible, cryptographic seal tying the modern signatures to the
same proof set referenced by the Patoshi continuity suite.

## 4) Anchor the replay to the timestamped Patoshi dossier

Optionally verify the OpenTimestamps receipt that notarises the Patoshi runbook
before or after running the steps above:

```bash
base64 -d proofs/patoshi_pattern_timestamped_attestation.md.ots.base64 > /tmp/patoshi.ots
ots verify /tmp/patoshi.ots proofs/patoshi_pattern_timestamped_attestation.md
```

The receipt ties the replayed signatures, catalogue output, and Merkle digest
back to the timestamped Patoshi dossier already committed to this repository.
