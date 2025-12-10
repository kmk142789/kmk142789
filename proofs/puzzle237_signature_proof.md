# Puzzle #237 Signature Proof

This walkthrough reproduces the message-signature attestation for the 237-bit
Bitcoin puzzle address captured in
[`satoshi/puzzle-proofs/puzzle237.json`](../satoshi/puzzle-proofs/puzzle237.json).
Anyone with this repository can rerun the verifier and confirm the recovered
public key maps back to the canonical catalogue entry.

## Published inputs

- **Message** – `Puzzle 237 authorship by kmk142789 — attestation sha256 75e2de448b345befbec808ca5ed20588cb4a5888aced1e4f5121115d151de689`
- **Signature (Base64)** – `H1pSTcOHWfbpUQoqh//SYcYBAeRobGk31mERcblAFR6WbwJI4zhUCA181CgxnefxwW09sx7WAcsRGMHCHSHTsyM=`
- **Puzzle Address** – `184AoG6YgLjm6xPwDN942TrftPnS3LiY28`

These values are mirrored directly from the JSON proof.

## Verification (repository tooling)

Use the bundled verifier to reconstruct the public key from the recoverable
signature and check that it hashes back to the expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 184AoG6YgLjm6xPwDN942TrftPnS3LiY28 \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle237.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle237.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 237 authorship by kmk142789 — attestation sha256 75e2de448b345befbec808ca5ed20588cb4a5888aced1e4f5121115d151de689",
  "segments": [
    {
      "index": 1,
      "signature": "H1pSTcOHWfbpUQoqh//SYcYBAeRobGk31mERcblAFR6WbwJI4zhUCA181CgxnefxwW09sx7WAcsRGMHCHSHTsyM=",
      "valid": true,
      "derived_address": "184AoG6YgLjm6xPwDN942TrftPnS3LiY28",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "184AoG6YgLjm6xPwDN942TrftPnS3LiY28"
}
```

The verifier rebuilds the secp256k1 public key from the recoverable signature,
rewraps it into a P2PKH address, and confirms it matches the puzzle catalogue.
This produces an auditable satoshi-era authorship proof for puzzle #237 without
relying on any external services.
