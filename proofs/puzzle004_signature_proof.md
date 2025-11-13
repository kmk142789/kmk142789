# Puzzle #4 Signature Proof

This note publishes a reproducible verification of the Bitcoin Signed Message
attached to Puzzle #4 (`1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e`). The attestation is
stored in [`satoshi/puzzle-proofs/puzzle004.json`](../satoshi/puzzle-proofs/puzzle004.json)
and ties the message directly to the long-standing solution catalogued in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H3P7kliVDYDtTNTQnTYEDsaDW1ntv9bJTvM1JdrHnwqyBLoaIjuIdyjbZPDbads8doRe1wc0eOYuBh3wF67XW/w=`
- **Puzzle address** – `1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e`

These values are copied verbatim from the JSON artefact.

## Repository verification

Use the bundled CLI to check the published signature against the declared
message and address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle004.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle004.json)" \
  --pretty
```

The command recovers a secp256k1 public key from the base64 payload, converts it
into a P2PKH address, and confirms the result matches the published puzzle
address. The JSON emitted by the verifier is saved in
[`verifier/results/1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e.json`](../verifier/results/1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e.json)
and looks like this:

```json
{
  "puzzle": 4,
  "address": "1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e",
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "H3P7kliVDYDtTNTQnTYEDsaDW1ntv9bJTvM1JdrHnwqyBLoaIjuIdyjbZPDbads8doRe1wc0eOYuBh3wF67XW/w=",
      "valid": true,
      "derived_address": "1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1
}
```

## Cross-checking the canonical solution

Entry `.[3]` inside `satoshi/puzzle_solutions.json` records the official
solution for the four-bit puzzle slot. The address, compressed public key, and
HASH160 fingerprint all match the verifier output above, providing an
independent reference that any auditor can inspect with:

```bash
jq '.[3]' satoshi/puzzle_solutions.json
```

---

Publishing this trace alongside the raw signature locks another Satoshi-era
puzzle into the attestation set, delivering an instantly reproducible proof that
requires nothing more than the math already bundled with the repository.
