# Satoshi Puzzle Stack Proof — Multi-Key Signature Relay

This runbook layers three independent Bitcoin puzzle attestations with the
existing Merkle and catalogue tooling so investigators can replay a vertical
slice of the Satoshi-era key material without leaving the repository.

## 1. Inspect the canonical puzzle entries

Confirm the official puzzle catalogue lists the addresses for the 15-, 18-, and
20-bit slots:

```bash
jq '.[] | select(.bits == 15 or .bits == 18 or .bits == 20) | {bits, address}' \
  satoshi/puzzle_solutions.json
```

The command prints the recorded addresses `1QCbW9HWnwQWiQqVo5exhAnmfqKRrCRsvW`,
`1GnNTmTVLZiqQfLbAdp9DVdicEnB5GoERE`, and `1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum`,
providing the canonical targets for the signatures validated below.

## 2. Validate the Puzzle #15 recoverable signature

Use the bundled verifier to decode the attestation stored in
[`satoshi/puzzle-proofs/puzzle015.json`](../satoshi/puzzle-proofs/puzzle015.json):

```bash
python -m verifier.verify_puzzle_signature \
  --address 1QCbW9HWnwQWiQqVo5exhAnmfqKRrCRsvW \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle015.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle015.json)" \
  --pretty
```

The CLI reports `valid_segment_count: 1` with the recovered address matching the
catalogue entry, proving the 15-bit puzzle key still signs fresh Bitcoin
messages without touching the on-chain balance.

## 3. Decode the stacked Puzzle #18 signature chain

Puzzle #18 ships a concatenated set of Base64 fragments that each recover to the
same address. Verify all segments in one pass:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1GnNTmTVLZiqQfLbAdp9DVdicEnB5GoERE \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle018.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle018.json)" \
  --pretty
```

Expect multiple entries under `segments`, all marked `valid: true` with identical
`derived_address` values. This demonstrates that every fragment embedded in the
proof catalogues back to the published puzzle solution.

## 4. Reconfirm the 20-bit key

Mirror the check for the 20-bit slot to show the larger-balance puzzle is under
the same custodial control:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle020.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle020.json)" \
  --pretty
```

Once again the recovered address mirrors the catalogue entry, extending the
Satoshi lineage through the higher-value tranche of the historical puzzle set.

## 5. Catalogue and hash the verified proofs

Roll the three JSON entries (plus any others of interest) into an auditable
report using the existing catalogue helper:

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob puzzle015.json \
  --glob puzzle018.json \
  --glob puzzle020.json \
  --pretty
```

The resulting JSON summarises how many stacked segments were checked, how many
validated, and which addresses they correspond to. Close the loop by recomputing
the Merkle root for the entire proof set and comparing it to the committed
history:

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Matching digests show that the attestation tree still commits to the exact proof
files verified in the earlier steps, providing a tamper-evident checksum across
the full catalogue.

---

By chaining the canonical puzzle registry, three independent recoverable
signatures, the catalogue census, and the Merkle anchor, this runbook adds
another reproducible Satoshi proof path that any researcher can replay within
minutes.
