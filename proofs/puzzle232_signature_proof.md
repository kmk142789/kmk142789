# Puzzle #232 Signature Proof

This memo documents the reproducible verification of the 232-bit Bitcoin
puzzle attestation stored in
[`satoshi/puzzle-proofs/puzzle232.json`](../satoshi/puzzle-proofs/puzzle232.json).
The recovered key resolves to the canonical address referenced by the
[`attestations/puzzle-232-authorship.json`](../attestations/puzzle-232-authorship.json)
record.

## Published inputs

- **Message** – `Puzzle 232 authorship by kmk142789 — attestation sha256 c60ea766814b2649365c6b87a55fb3b9a7d5aaff1a9362af547ffd2e51c2e24c`
- **Signature (Base64)** – `IDD3Z+0MeejKs+mGObrVSD/9euVxWLILx/le7wwLzP9cQkXgvuI1fSXYyZ9VQTYjktFTvqMsP5La/D8GNhWsE4c=`
- **Puzzle Address** – `1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1`

## Verification (repository tooling)

Use the bundled verifier to confirm the recoverable signature resolves to the
expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1 \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle232.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle232.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 232 authorship by kmk142789 — attestation sha256 c60ea766814b2649365c6b87a55fb3b9a7d5aaff1a9362af547ffd2e51c2e24c",
  "segments": [
    {
      "index": 1,
      "signature": "IDD3Z+0MeejKs+mGObrVSD/9euVxWLILx/le7wwLzP9cQkXgvuI1fSXYyZ9VQTYjktFTvqMsP5La/D8GNhWsE4c=",
      "valid": true,
      "derived_address": "1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1"
}
```

The verifier reconstructs the secp256k1 public key from the recoverable
signature and confirms its Base58Check encoding matches the puzzle address.
Anyone with this repository can replay the steps above and independently
audit the satoshi-era authorship proof for puzzle #232.
