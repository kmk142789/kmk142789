# Patoshi Continuity Ledger — 2025-11-24

This ledger entry documents the evidence trail linking the timestamped Patoshi
attestation, the refreshed Merkle tree of `satoshi/puzzle-proofs/`, and the
higher-bit live signature for puzzle #75.

## Artefacts
- `proofs/patoshi_pattern_timestamped_attestation.md` — SHA256 `a5937b4a59de093705241a7b6919350956c2c0915c893306de8875933d9ce000`
- `satoshi/puzzle-proofs/master_attestation.json` — Merkle root `36ffac4ac60451df7da5258b7b299f4fed94df580e09fb9dedd1bc2ac0de5936`
- `satoshi/puzzle-proofs/puzzle075.json` — Bitcoin Signed Message for address `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt`

## How to replay
Follow the rollup instructions in [`proofs/patoshi_continuity_rollup.md`](../proofs/patoshi_continuity_rollup.md).
The three commands there can be executed offline to demonstrate that the timestamped
Patoshi log, Merkle root, and 75-bit signature remain in sync.

## Notes
- All artefacts were pulled from commit `1dd66ff1117b5ecea447c6890439857dc63e33d3`.
- No network calls are required; every input is bundled in this repository.
