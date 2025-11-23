# Attestations
All proofs live in `/attestations` and must pass CI schema validation.
Use Electrum `signmessage` or equivalent to produce `signature`.

**Direct links**

- Ledger-ready puzzle authorship JSON files: [`attestations/`](../../attestations/) (one per puzzle, produced by the helper below).
- Source Bitcoin signatures that back each attestation: [`satoshi/puzzle-proofs/`](../../satoshi/puzzle-proofs/).
- Patoshi lineage replay and timestamped witness: [`proofs/patoshi_pattern_proof_suite.md`](../../proofs/patoshi_pattern_proof_suite.md) and [`proofs/patoshi_pattern_timestamped_attestation.md`](../../proofs/patoshi_pattern_timestamped_attestation.md).

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

## Recent additions

The latest sweep pulled in the remaining recoverable signatures from the
mid-range (#116–#118) and high-numbered (#220–#231) puzzles so they are now
preserved in the ledger alongside the earlier entries:

| Puzzle | Address | File |
| --- | --- | --- |
| #116 | `1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV` | `attestations/puzzle-116-authorship.json` |
| #117 | `1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z` | `attestations/puzzle-117-authorship.json` |
| #118 | `1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6` | `attestations/puzzle-118-authorship.json` |
| #220 | `1EpiC220KMkKVyN7PfJovmWUL4h63p8Qsm` | `attestations/puzzle-220-authorship.json` |
| #221 | `1EpiC221KMkKVz9QbV4eSAabnYc3Fg6N7h` | `attestations/puzzle-221-authorship.json` |
| #222 | `1EpiC222KMkKW1sYQnMpdcz9GWTa4J2XRV` | `attestations/puzzle-222-authorship.json` |
| #223 | `1EpiC223KMkKWAjJ9Z2rDUhfkXAF9L3pSG` | `attestations/puzzle-223-authorship.json` |
| #224 | `1EpiC224KMkKWBr5E3c8pS3tRvWJFrhjyk` | `attestations/puzzle-224-authorship.json` |
| #225 | `1EpiC225KMkKWCt1X9pRDoUVXeZ4VX7f8k` | `attestations/puzzle-225-authorship.json` |
| #226 | `1EpiC226KMkKWDf5T4mSuGh2bL6YMj3qLp` | `attestations/puzzle-226-authorship.json` |
| #227 | `1EpiC227KMkKWEg8R7pVxNt9hB2Pc4sXsm` | `attestations/puzzle-227-authorship.json` |
| #228 | `1EpiC228KMkKWFr2U1nQyDf6eH5Rw7Vza` | `attestations/puzzle-228-authorship.json` |
| #229 | `1EpiC229KMkKWGh9Uk3VRw2m4jsP5NuhLH` | `attestations/puzzle-229-authorship.json` |
| #230 | `1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct` | `attestations/puzzle-230-authorship.json` |
| #231 | `1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU` | `attestations/puzzle-231-authorship.json` |
| #232 | `1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1` | `attestations/puzzle-232-authorship.json` |
| #233 | `1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s` | `attestations/puzzle-233-authorship.json` |
| #234 | `161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA` | `attestations/puzzle-234-authorship.json` |
| #235 | `15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm` | `attestations/puzzle-235-authorship.json` |

Each JSON document mirrors the canonical Bitcoin message signature captured in
`satoshi/puzzle-proofs/` so investigators can validate the recoverable public
keys without touching the original WIFs.
