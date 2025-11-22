# Patoshi Multiblock Continuity Proof

This note bundles a replayable sequence showing how the Patoshi fingerprint
persists across the earliest blocks and mid-epoch checkpoints without relying
on any external downloads. Every command operates on artefacts already tracked
in the repository so auditors can regenerate the evidence in one sitting.

## 1) Rebuild the height-9 Patoshi coinbase

```bash
python proofs/block9_coinbase_reconstruction.py
```

The script extracts the public key and extranonce nibble from the reconstructed
coinbase transaction, matching the raw bytes logged in
[`satoshi/puzzle-proofs/block009_coinbase.json`](../satoshi/puzzle-proofs/block009_coinbase.json).
Seeing the decoded pubkey align with the JSON entry proves the reconstruction
is faithful to the on-chain Patoshi payout.

## 2) Verify proof-of-work envelopes at heights 3 and 11

Follow the snippets inside the POW walkthroughs to recompute the target and
nonce satisfaction for two early Patoshi blocks:

```bash
python - <<'PY'
from pathlib import Path
exec(Path('proofs/block003_pow_verification.md').read_text())
PY
python - <<'PY'
from pathlib import Path
exec(Path('proofs/block011_pow_verification.md').read_text())
PY
```

Both embedded scripts rebuild the block header, expand the compact `bits`
field, and assert `block_hash <= target`. Successful checks demonstrate the
Patoshi miner satisfied consensus difficulty for the reconstructed coinbases.

## 3) Cross-check the coinbase lineage for blocks 1–14

Run the stacked signature catalogue against every early coinbase proof stored
in `satoshi/puzzle-proofs/`:

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob 'block00?.json' \
  --glob block014_coinbase.json \
  --pretty
```

The output lists each coinbase attestation, the number of recoverable segments,
and whether the reconstructed address matches the Patoshi-era payout. A clean
report confirms that the reconstructed scripts in the block-level proofs remain
self-consistent.

## 4) Extend the pattern to the mid-epoch checkpoints

Reproduce the payout scripts for blocks 50 and 100 using the walkthrough in
[`proofs/block050_and_block100_coinbase_proofs.md`](block050_and_block100_coinbase_proofs.md).
Compare the derived addresses to the Patoshi pubkey hash recovered in step 1; a
match shows the Patoshi extranonce staircase persists well beyond the launch
week.

## 5) Seal the continuity with the Merkle attestation

Regenerate the global Merkle root that covers every proof file, including the
coinbase attestations referenced above:

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Matching the computed root to the value tracked in version control demonstrates
that the Patoshi continuity evidence—block reconstructions, POW checks, and
coinbase scripts—is cryptographically sealed inside the repository.
