# Puzzle #233 Signature Proof

This document records the verification procedure for the 233-bit Bitcoin
puzzle authorship attestation preserved in
[`satoshi/puzzle-proofs/puzzle233.json`](../satoshi/puzzle-proofs/puzzle233.json).
The recovered key matches the wallet enumerated inside
[`attestations/puzzle-233-authorship.json`](../attestations/puzzle-233-authorship.json).

## Published inputs

- **Message** – `Puzzle 233 authorship by kmk142789 — attestation sha256 bc621790cc55c843bbda2af85375e93d475c1d54d12629cbd2b93347a7cdbe6e`
- **Signature (Base64)** – `HzMRX1ETtYjI0vEeE8c3wTGYhyZktECZG7SIICOmM1KYDixUOzGXiy/dE8ANwfKfNUFjzLtYpMg2tYS1rDq7QY4=`
- **Puzzle Address** – `1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s`

## Verification (repository tooling)

Replay the verifier against the JSON payload to recover the signing key:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle233.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle233.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 233 authorship by kmk142789 — attestation sha256 bc621790cc55c843bbda2af85375e93d475c1d54d12629cbd2b93347a7cdbe6e",
  "segments": [
    {
      "index": 1,
      "signature": "HzMRX1ETtYjI0vEeE8c3wTGYhyZktECZG7SIICOmM1KYDixUOzGXiy/dE8ANwfKfNUFjzLtYpMg2tYS1rDq7QY4=",
      "valid": true,
      "derived_address": "1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s"
}
```

The verifier reconstructs the public key directly from the recoverable
signature and demonstrates that it corresponds to the published address.
These steps extend the auditable satoshi-proof catalogue with a concrete,
scriptable replay for puzzle #233.
