# Satoshi Proof — Quick Verification Index

This short index points to the repository’s reproducible, offline proof chain
for the Satoshi lineage. Use it when you need a concise, end-to-end path without
digging through the full documentation set.

## Start here: full offline chain

Follow the five-step walkthrough in
[`proofs/satoshi_groundbreaking_proof.md`](satoshi_groundbreaking_proof.md). It
verifies:

1. The README timestamp anchor (OpenTimestamps receipt).
2. The genesis block reconstruction (block hash + payout address).
3. The Block 0 reactivation signature replay.
4. The Puzzle #1 genesis broadcast signature replay.
5. The master attestation Merkle root rebuild.

## Supporting proof set

If you want deeper coverage, these supporting docs extend the chain with
additional Satoshi-era blocks and puzzle signatures:

- [`proofs/satoshi_irrefutable_chain.md`](satoshi_irrefutable_chain.md)
- [`proofs/satoshi_continuity_proof.md`](satoshi_continuity_proof.md)
- [`proofs/satoshi_puzzle_stack_proof.md`](satoshi_puzzle_stack_proof.md)
- [`proofs/satoshi_puzzle_expansion_proof.md`](satoshi_puzzle_expansion_proof.md)
- [`proofs/satoshi_relay_proof.md`](satoshi_relay_proof.md)

## Artifact locations

The underlying JSON proofs referenced by the walkthroughs live under:

- `satoshi/puzzle-proofs/` for puzzle signatures, coinbase reconstructions, and
  the aggregated `master_attestation.json`.
- `proofs/` for step-by-step verification playbooks.
