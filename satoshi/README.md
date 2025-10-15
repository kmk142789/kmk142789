# Satoshi Puzzle Proofs

This directory collects per-puzzle message-signature attestations.

Each entry in [`puzzle-proofs/`](puzzle-proofs/) is a JSON document with the following fields:

- `puzzle`: numerical identifier for the Bitcoin puzzle claim
- `address`: associated Bitcoin address for the signature
- `message`: exact message string that was signed
- `signature`: base64-encoded ECDSA signature produced by the referenced key

## Entries

- `puzzle003.json` — Puzzle #3 authorship attestation for address `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`.
- `puzzle007.json` — Puzzle #7 authorship attestation for address `19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA`.
- `puzzle015.json` — Puzzle #15 authorship attestation for address `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`.
