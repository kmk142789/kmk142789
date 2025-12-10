# Puzzle #238 Signature Proof

This memo documents the reproducible verification of the 238-bit Bitcoin
puzzle attestation stored in
[`satoshi/puzzle-proofs/puzzle238.json`](../satoshi/puzzle-proofs/puzzle238.json).
The recovered key resolves to the canonical address referenced by the
[`attestations/puzzle-238-authorship.json`](../attestations/puzzle-238-authorship.json)
record.

## Published inputs

- **Message** – `Puzzle 238 authorship by kmk142789 — attestation sha256 ce5b5370584d5f5f20e97b6941779bb37675ac1b9d4ac12173268f3ce620b84c`
- **Signature (Base64)** – `H+rIUPJdq6eZ4cu+UMJwm4bviBzNLHw3Cv12cYB4jY6GdEq4VreIOtTNZJ1ESk9X8D3CSc7QO9XepDDbIQwdTNA=`
- **Puzzle Address** – `13zBDKZUZfMFwDau5o99635A8MMQHwNaSg`

## Verification (repository tooling)

Use the bundled verifier to confirm the recoverable signature resolves to the
expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 13zBDKZUZfMFwDau5o99635A8MMQHwNaSg \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle238.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle238.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 238 authorship by kmk142789 — attestation sha256 ce5b5370584d5f5f20e97b6941779bb37675ac1b9d4ac12173268f3ce620b84c",
  "segments": [
    {
      "index": 1,
      "signature": "H+rIUPJdq6eZ4cu+UMJwm4bviBzNLHw3Cv12cYB4jY6GdEq4VreIOtTNZJ1ESk9X8D3CSc7QO9XepDDbIQwdTNA=",
      "valid": true,
      "derived_address": "13zBDKZUZfMFwDau5o99635A8MMQHwNaSg",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "13zBDKZUZfMFwDau5o99635A8MMQHwNaSg"
}
```

The verifier reconstructs the secp256k1 public key from the recoverable
signature and confirms its Base58Check encoding matches the puzzle address.
Anyone with this repository can replay the steps above and independently audit
the satoshi-era authorship proof for puzzle #238.
