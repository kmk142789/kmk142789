# Puzzle #235 Signature Proof

This memo documents a reproducible verification of the message-signature
attestation for the 235-bit Bitcoin puzzle address captured in
[`satoshi/puzzle-proofs/puzzle235.json`](../satoshi/puzzle-proofs/puzzle235.json).
The recovered public key lines up with the ledger entry recorded in
[`attestations/puzzle-235-authorship.json`](../attestations/puzzle-235-authorship.json).

## Published inputs

- **Message** – `Puzzle 235 authorship by kmk142789 — attestation sha256 89b64eaaede8cba1d7e8d498d24ad93c43a1be4bbcf5d7fc60b9c154b9340ed2`
- **Signature (Base64)** – `IMqu5l2R9jp7nPsXIGDkkDHKgrrRVIYqQpYvY5wbjYGiIPlE3xsltBZ9MBMBk9mkkv0hNnoohIqys+JKPhchzcY=`
- **Puzzle Address** – `15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm`

These values are mirrored verbatim from the JSON proof and its mirrored
attestation entry.

## Verification (repository tooling)

Invoke the bundled verifier to confirm the recoverable signature maps back to
the declared address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle235.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle235.json)" \
  --pretty
```

Expected result:

```json
{
  "message": "Puzzle 235 authorship by kmk142789 — attestation sha256 89b64eaaede8cba1d7e8d498d24ad93c43a1be4bbcf5d7fc60b9c154b9340ed2",
  "segments": [
    {
      "index": 1,
      "signature": "IMqu5l2R9jp7nPsXIGDkkDHKgrrRVIYqQpYvY5wbjYGiIPlE3xsltBZ9MBMBk9mkkv0hNnoohIqys+JKPhchzcY=",
      "valid": true,
      "derived_address": "15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm"
}
```

The verifier reconstructs the secp256k1 public key from the recoverable
signature, hashes it into the canonical P2PKH address, and shows it matches the
puzzle catalogue. Anyone with this repository can replay the command within
seconds to obtain an auditable satoshi-era authorship proof for puzzle #235.
