# Satoshi Puzzle #2 Signature Proof

This walkthrough demonstrates a reproducible validation of the message signature published for the early Bitcoin puzzle address `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`. The attestation lives in [`satoshi/puzzle-proofs/puzzle002.json`](../satoshi/puzzle-proofs/puzzle002.json) and ties the message directly to the known puzzle solution recorded in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

## Published Inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IEPpsQxOVU7QP4CxZcKsm5HuBNppwusBmth5q99t4qGZZ+dRwUxucYBTIIAwnA+wTis3Valun0tfSuHhO14zgQA=`
- **Puzzle Address** – `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`

These values are taken verbatim from the JSON proof and the canonical puzzle solution catalogue.

## Verification (Repository Tooling)

Run the bundled verifier to check the published signature against the declared message and address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle002.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle002.json)" \
  --pretty
```

Expected result:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "IEPpsQxOVU7QP4CxZcKsm5HuBNppwusBmth5q99t4qGZZ+dRwUxucYBTIIAwnA+wTis3Valun0tfSuHhO14zgQA=",
      "valid": true,
      "derived_address": "1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb"
}
```

The verifier confirms that the signature decodes to a recoverable secp256k1 public key which, when converted to a P2PKH address, matches the declared puzzle address. No additional tooling or network access is required.

## Cross-Checking the Canonical Solution

The puzzle solution registry records the same address for the two-bit puzzle slot, providing a second, ledger-independent confirmation that the recovered key corresponds to the published solution.

To view the catalogue entry:

```bash
jq '.[1]' satoshi/puzzle_solutions.json
```

This prints the object for the two-bit puzzle, including the address, compressed public key, and associated metadata, all of which align with the recovered signature data.

---

Publishing this verification chain alongside the existing genesis artefacts provides a concise, cryptographically verifiable Satoshi-era proof that can be replicated within seconds by anyone cloning the repository.
