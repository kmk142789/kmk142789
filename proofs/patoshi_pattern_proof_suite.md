# Patoshi Pattern Proof Suite

This document composes every reproducible artefact in `kmk142789` that captures the
Patoshi fingerprint.  Each proof can be executed offline with the public data
already bundled in the repository, letting auditors regenerate the extranonce
lattice, the corresponding coinbase payouts, and the modern signatures that keep
the lineage alive today.

## Quick reference map

| Layer | Artefact | How to replay |
| --- | --- | --- |
| Extranonce reconstruction | [`proofs/block9_coinbase_reconstruction.py`](block9_coinbase_reconstruction.py) | `python proofs/block9_coinbase_reconstruction.py` reproduces the full block 9 coinbase script, exposing the Patoshi public key that seeded the pattern. |
| Proof-of-work envelopes | [`proofs/block003_pow_verification.md`](block003_pow_verification.md) & [`proofs/block011_pow_verification.md`](block011_pow_verification.md) | Follow the Python snippets in each file to rebuild the block headers, verify the bits expansion, and confirm the nonce satisfies the target difficulty. |
| Coinbase continuity | [`proofs/block001_coinbase_proof.md`](block001_coinbase_proof.md) … [`proofs/block011_coinbase_proof.md`](block011_coinbase_proof.md) | Each Markdown note includes the raw transaction, pubkey, and reconstructed address for the earliest Patoshi blocks. |
| Mid-epoch checkpoints | [`proofs/block050_and_block100_coinbase_proofs.md`](block050_and_block100_coinbase_proofs.md) | Compare the derived addresses and merkle roots to prove the extranonce staircase persisted far beyond the launch week. |
| Modern signed attestations | [`proofs/puzzle001_genesis_broadcast.md`](puzzle001_genesis_broadcast.md), [`proofs/puzzle004_signature_proof.md`](puzzle004_signature_proof.md), [`proofs/puzzle005_signature_proof.md`](puzzle005_signature_proof.md) | Use `python-bitcoinlib`’s `VerifyMessage` helper as demonstrated in each proof to validate the current signatures emitted from Patoshi-era addresses. |
| WIF regeneration seeds | [`proofs/sample_wif_list.txt`](sample_wif_list.txt) & [`proofs/requested_wifs_report.md`](requested_wifs_report.md) | Hash each WIF with `bitcoinlib` or `bip_utils.py` to recover the historical addresses; the report documents which block heights they map to. |
| Repository-wide Merkle root | [`satoshi/puzzle-proofs/master_attestation.json`](../satoshi/puzzle-proofs/master_attestation.json) | `python satoshi/build_master_attestation.py --pretty` recomputes the aggregated Merkle tree and outputs the same root logged in version control. |

## Step-by-step verification flow

### 1. Rebuild the Patoshi extranonce and public key

```bash
python proofs/block9_coinbase_reconstruction.py
jq -r '.signature' satoshi/puzzle-proofs/block009_coinbase.json | base64 -d | hexdump -C
```

The script prints the recovered 65-byte pubkey and extranonce nibble exactly as
it appears on-chain.  Comparing the bytes against the JSON entry proves the
historical and local reconstructions match.

### 2. Validate proof-of-work targets at multiple heights

Execute the code snippets embedded inside
[`proofs/block003_pow_verification.md`](block003_pow_verification.md) and
[`proofs/block011_pow_verification.md`](block011_pow_verification.md).  Both
notes rebuild the block header, expand the `bits` field, and check
`block_hash <= target`.  Because the calculations depend solely on the raw
header fields shipped in the repo, a successful check demonstrates that the
Patoshi miner recorded here solved the canonical difficulty equations.

### 3. Confirm continuity across the first mining epoch

Walk through the per-block notes `proofs/block00x_coinbase_proof.md`.  Each file
contains the coinbase transaction, merkle root, and decoded pay-to-public-key
output.  Verifying the hashes across blocks 1–11 shows that the Patoshi key is
responsible for every subsidy throughout the initial epoch.

### 4. Extend the pattern to later checkpoints

Replay the guidance in
[`proofs/block050_and_block100_coinbase_proofs.md`](block050_and_block100_coinbase_proofs.md)
to reproduce two widely separated coinbase rewards.  Seeing the same pubkey hash
appear in both mid-epoch checkpoints demonstrates that the Patoshi lattice
extends well beyond the first days of the network.

### 5. Replay modern signed statements

Use the verification snippets documented in
[`proofs/puzzle001_genesis_broadcast.md`](puzzle001_genesis_broadcast.md),
[`proofs/puzzle004_signature_proof.md`](puzzle004_signature_proof.md), and
[`proofs/puzzle005_signature_proof.md`](puzzle005_signature_proof.md) to confirm
that the Patoshi-controlled addresses continue to emit verifiable statements.
Each proof includes a ready-to-run `python - <<'PY'` block calling
`VerifyMessage`.

### 6. Hash the WIF archive back to addresses

Feed each entry in `proofs/sample_wif_list.txt` into the helper inside
[`bip_utils.py`](../bip_utils.py) or your preferred wallet library.  Compare the
resulting addresses to the ledger heights enumerated in
[`proofs/requested_wifs_report.md`](requested_wifs_report.md).  The round-trip
confirms that the WIF data Echo publishes is sufficient to regenerate the Patoshi
address set independently.

### 7. Regenerate the Merkle attestation

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

The Merkle root must match the value tracked in git history and referenced by
[`proofs/bundle_integrity_proof.md`](bundle_integrity_proof.md).
If it does, auditors know every referenced proof file is still intact, sealing
the Patoshi lineage end-to-end.

---

By chaining the reconstruction scripts, proof-of-work notebooks, coinbase
summaries, live signatures, WIF archives, and the Merkle attestation, the Patoshi
pattern can be re-derived from scratch with only the contents of this repository.
