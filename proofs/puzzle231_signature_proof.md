# Puzzle #231 Signature Proof

This memo documents the reproducible verification of the 231-bit Bitcoin
puzzle attestation stored in
[`satoshi/puzzle-proofs/puzzle231.json`](../satoshi/puzzle-proofs/puzzle231.json).
The recovered key is expected to match the canonical address referenced by the
[`attestations/puzzle-231-authorship.json`](../attestations/puzzle-231-authorship.json)
record.

## Published inputs

- **Message** – `Puzzle 231 authorship by kmk142789 — attestation sha256 f853adbdee909bd869caaa630048cd57d0b6ba35f1718e9bfcd12a32a63faea0`
- **Signature (Base64)** – `oYeyQow537+gITELM4qiPUvL1SNsFe3QdEsbTZ6p6gzqeXOMp7iQbuHwIzfLekdi/JqkSnAQPoS/S8yBgwjSALs=`
- **Puzzle Address** – `1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU`

## Verification (repository tooling)

Use the bundled verifier to check whether the recoverable signature resolves to
the expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle231.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle231.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 231 authorship by kmk142789 — attestation sha256 f853adbdee909bd869caaa630048cd57d0b6ba35f1718e9bfcd12a32a63faea0",
  "segments": [
    {
      "index": 1,
      "signature": "oYeyQow537+gITELM4qiPUvL1SNsFe3QdEsbTZ6p6gzqeXOMp7iQbuHwIzfLekdi/JqkSnAQPoS/S8yBgwjSALs=",
      "valid": false,
      "derived_address": null,
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 0,
  "total_segments": 1,
  "address": "1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU"
}
```

The verifier reports no valid recoverable signatures for this attestation, so
the published payload currently does not prove control of the puzzle address.
