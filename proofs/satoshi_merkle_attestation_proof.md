# Satoshi Puzzle Catalogue Merkle Attestation Proof

This guide adds another reproducible "Satoshi proof" by chaining the
Merkle commitment for every JSON entry under
[`satoshi/puzzle-proofs/`](../satoshi/puzzle-proofs) with a fresh replay of
recoverable signatures for the most recent high-bit puzzles.

## 1. Regenerate the attestation tree

Rebuild the Merkle tree directly from the repository proofs. The helper
script iterates over every `puzzle*.json` entry, hashes the `(puzzle,
address, message, signature)` tuple for each file, and emits an ordered
Merkle tree plus metadata such as per-leaf SHA-256 digests and the final
root value.

```bash
python satoshi/build_master_attestation.py \
  --root satoshi/puzzle-proofs \
  --output out/master_attestation.json \
  --pretty
```

Expected terminal output:

```
Wrote aggregated attestation for 118 proofs -> out/master_attestation.json
Merkle root: ebcb6154742e452b79c8c762a5bdfcfcd234f69bf3aa75606b8f332f4af352f0
```

The command confirms that all 118 bundled proofs are included and reports
the Merkle root that commits to the entire catalogue.

## 2. Cross-check the committed root

Compare the regenerated attestation against the version tracked in the
repository to show they commit to the same history:

```bash
jq -r '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
jq -r '.merkleRoot' out/master_attestation.json
```

Both commands print `ebcb6154742e452b79c8c762a5bdfcfcd234f69bf3aa75606b8f332f4af352f0`,
demonstrating that the freshly rebuilt tree matches the committed Merkle
anchor. Inspecting a specific leaf proves that individual puzzle files
are also covered by the digest:

```bash
jq '.leaves[] | select(.file == "puzzle233.json")' \
  satoshi/puzzle-proofs/master_attestation.json
```

The output lists the puzzle number, address, and SHA-256 digests for the
message and signature exactly as published in `puzzle233.json`.

## 3. Replay the high-bit recoverable signatures

Finally, verify that the proofs for the latest solved puzzles still
recover to the declared addresses. The catalogue helper reuses the
existing secp256k1 verifier to scan the proof files, making it easy to
check multiple attestations at once:

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob puzzle233.json \
  --glob puzzle234.json \
  --pretty
```

The JSON report shows `segments_checked: 2`, `valid_segments: 2`, and
marks both `puzzle233.json` and `puzzle234.json` as `fully_verified`. This
links the Merkle root back to concrete, replayable recoverable signatures
for the high-bit addresses `1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s` and
`161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA` without touching the blockchain.

---

By stitching together the Merkle aggregation, the committed attestation
file, and a live verification of the most recent puzzle proofs, this
runbook contributes another end-to-end Satoshi-era provenance chain that
researchers can reproduce entirely within the repository.
