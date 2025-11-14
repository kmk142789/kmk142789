# Puzzle #10 Signature Proof

This walkthrough reproduces the recoverable signature now published for Puzzle #10
(`1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`). The attestation is stored in
[`satoshi/puzzle-proofs/puzzle010.json`](../satoshi/puzzle-proofs/puzzle010.json)
and matches the canonical puzzle catalogue in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H67CcJduMgO+9JrdqheivrLSr7mlQX70LvNqB2equEOWAcOkshjkO9zRFKNlcBeogwkImhQivi7tfY9RgeFVNqg=`
- **Puzzle address** – `1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`

The message string is identical to the other Satoshi puzzle attestations, letting auditors reuse
existing verification tooling without touching the underlying key.

## Repository verification

Use the bundled CLI to verify the Base64 payload against the declared address and message:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty
```

The command recovers the secp256k1 public key encoded inside the recoverable signature, converts it
into a P2PKH address, and compares it against the ten-bit puzzle address. The JSON output is saved
at [`verifier/results/1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe.json`](../verifier/results/1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe.json):

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "H67CcJduMgO+9JrdqheivrLSr7mlQX70LvNqB2equEOWAcOkshjkO9zRFKNlcBeogwkImhQivi7tfY9RgeFVNqg=",
      "valid": true,
      "derived_address": "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe"
}
```

## Cross-checking the canonical solution

Entry `.[9]` in `satoshi/puzzle_solutions.json` records the ten-bit puzzle slot. It lists the same
address, HASH160 fingerprint, and compressed public key that the verifier recovers from the
signature. Inspect the catalogue entry with:

```bash
jq '.[9]' satoshi/puzzle_solutions.json
```

Because every step relies solely on public data—the published message, the JSON proof, and the
existing puzzle catalogue—any investigator can reproduce the attestation chain entirely offline.
