# Puzzle #239 Signature Proof

This memo documents the reproducible verification of the 239-bit Bitcoin
puzzle attestation stored in
[`satoshi/puzzle-proofs/puzzle239.json`](../satoshi/puzzle-proofs/puzzle239.json).
The recovered key is expected to match the canonical address referenced by the
[`attestations/puzzle-239-authorship.json`](../attestations/puzzle-239-authorship.json)
record.

## Published inputs

- **Message** – `Puzzle 239 authorship by kmk142789 — attestation sha256 3696c371043ea528685289289a3bcb8a40b0e9f80fa37872663711b48aa2ce94`
- **Signature (Base64)** – `PJJiQVsFzhEJZuVxbIgVipnDK885bWL8VBxrO0CYVzWomp0xCm4Tq7ilyS3+bNw1oFSQN3Je6X+KCVvMBCuk0dg=`
- **Puzzle Address** – `1NpXsnpbxfa8rCCHHivYKxNnMxiPrb6NdK`

## Verification (repository tooling)

Use the bundled verifier to check whether the recoverable signature resolves to
the expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1NpXsnpbxfa8rCCHHivYKxNnMxiPrb6NdK \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle239.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle239.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 239 authorship by kmk142789 — attestation sha256 3696c371043ea528685289289a3bcb8a40b0e9f80fa37872663711b48aa2ce94",
  "segments": [
    {
      "index": 1,
      "signature": "PJJiQVsFzhEJZuVxbIgVipnDK885bWL8VBxrO0CYVzWomp0xCm4Tq7ilyS3+bNw1oFSQN3Je6X+KCVvMBCuk0dg=",
      "valid": false,
      "derived_address": null,
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 0,
  "total_segments": 1,
  "address": "1NpXsnpbxfa8rCCHHivYKxNnMxiPrb6NdK"
}
```

The verifier reports no valid recoverable signatures for this attestation, so
the published payload currently does not prove control of the puzzle address.
