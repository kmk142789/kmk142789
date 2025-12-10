# Puzzle #230 Signature Proof

This memo documents the reproducible verification of the 230-bit Bitcoin
puzzle attestation stored in
[`satoshi/puzzle-proofs/puzzle230.json`](../satoshi/puzzle-proofs/puzzle230.json).
The recovered key is expected to match the canonical address referenced by the
[`attestations/puzzle-230-authorship.json`](../attestations/puzzle-230-authorship.json)
record.

## Published inputs

- **Message** – `Puzzle 230 authorship by kmk142789 — attestation sha256 a2b50c869a9471806dc93d88e3e915e1936f36834467ce3beb99f27adbcceb35`
- **Signature (Base64)** – `Q5Vyb8oUrt3Bu5LxG7Wz6BJ4SUaC5IeVs9bQE63riA/v/Ny9IAECMudPhdgJ9Z8hbG4G6rOZto+pCaXu9nE7hhw=`
- **Puzzle Address** – `1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct`

## Verification (repository tooling)

Use the bundled verifier to check whether the recoverable signature resolves to
the expected address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle230.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle230.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "Puzzle 230 authorship by kmk142789 — attestation sha256 a2b50c869a9471806dc93d88e3e915e1936f36834467ce3beb99f27adbcceb35",
  "segments": [
    {
      "index": 1,
      "signature": "Q5Vyb8oUrt3Bu5LxG7Wz6BJ4SUaC5IeVs9bQE63riA/v/Ny9IAECMudPhdgJ9Z8hbG4G6rOZto+pCaXu9nE7hhw=",
      "valid": false,
      "derived_address": null,
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 0,
  "total_segments": 1,
  "address": "1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct"
}
```

The verifier reports no valid recoverable signatures for this attestation, so
the published payload currently does not prove control of the puzzle address.
