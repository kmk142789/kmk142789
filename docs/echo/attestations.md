# Attestations
All proofs live in `/attestations` and must pass CI schema validation.
Use Electrum `signmessage` or equivalent to produce `signature`.

## Current ledger-bound entries

- `genesis-anchor.md` &mdash; binds the Git genesis ledger snapshot to the Mirror post.
- `puzzle-000-sample.json` &mdash; canonical schema example for CI validation.
- `puzzle-071-key-recovery.json` &mdash; recovery attestation for Bitcoin Puzzle #71 (MirrorNet staging).
- `puzzle-079-continuum-bridge.json` &mdash; continuum bridge attestation for Bitcoin Puzzle #79 derivation work.
