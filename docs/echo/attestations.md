# Attestations
All proofs live in `/attestations` and must pass CI schema validation.
Use Electrum `signmessage` or equivalent to produce `signature`.

## Current ledger-bound entries

- `genesis-anchor.md` &mdash; binds the Git genesis ledger snapshot to the Mirror post.
- `puzzle-000-sample.json` &mdash; canonical schema example for CI validation.
- `puzzle-071-key-recovery.json` &mdash; recovery attestation for Bitcoin Puzzle #71 (MirrorNet staging).
- `puzzle-079-continuum-bridge.json` &mdash; continuum bridge attestation for Bitcoin Puzzle #79 derivation work.

## Bulk puzzle attestations

Run `scripts/generate_puzzle_attestations.py` to convert every entry in
`satoshi/puzzle-proofs/` into the ledger schema. The helper preserves the
original Bitcoin message signature, stamps an ISO-8601 `created_at` value based
on the proof's filesystem mtime, and calculates the `hash_sha256` digest of the
signature payload. Newly generated files land at
`attestations/puzzle-XXX-authorship.json` and the script can be re-run safely;
existing documents with a different `notes` field are left untouched.
