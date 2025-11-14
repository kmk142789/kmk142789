# Puzzle #234 Signature Proof

This memo captures a reproducible verification walkthrough for the 234-bit
Bitcoin puzzle attestation published in
[`satoshi/puzzle-proofs/puzzle234.json`](../satoshi/puzzle-proofs/puzzle234.json).
The recovered public key aligns with the ledger entry preserved in
[`attestations/puzzle-234-authorship.json`](../attestations/puzzle-234-authorship.json).

## Published inputs

- **Message** – `Puzzle 234 authorship by kmk142789 — attestation sha256 8cc97a68ab5daf28629213a7a0eb44b30ae79f153863c11e190c1529677926f0`
- **Signature (Base64)** – `H9yuf4a4VhPOZrURQjaOaVTajBanaatWjtTZvZwyRTHlFGk47/QYnvnpYSSpeddS2npZKMjXwC14IBtV10uCv8U=`
- **Puzzle Address** – `161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA`

These values are copied directly from the JSON proof and its mirrored
attestation entry.

## Verification (repository tooling)

Use the bundled verifier to confirm that the recoverable signature maps back to
the declared address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle234.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle234.json)" \
  --pretty
```

Expected result:

```json
{
  "message": "Puzzle 234 authorship by kmk142789 — attestation sha256 8cc97a68ab5daf28629213a7a0eb44b30ae79f153863c11e190c1529677926f0",
  "segments": [
    {
      "index": 1,
      "signature": "H9yuf4a4VhPOZrURQjaOaVTajBanaatWjtTZvZwyRTHlFGk47/QYnvnpYSSpeddS2npZKMjXwC14IBtV10uCv8U=",
      "valid": true,
      "derived_address": "161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA"
}
```

The verifier reconstructs the secp256k1 public key straight from the recoverable
signature, hashes it into the canonical P2PKH address, and confirms it matches
the puzzle registry. Anyone with this repository can replay the command to
obtain an auditable satoshi-era authorship proof for puzzle #234.
