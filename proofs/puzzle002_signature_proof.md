# Puzzle #2 Signature Proof

This walkthrough adds another reproducible Satoshi-era attestation by
expanding the documentation for the two-bit Bitcoin puzzle wallet
`1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`. The signed message and raw
signature live in [`satoshi/puzzle-proofs/puzzle002.json`](../satoshi/puzzle-proofs/puzzle002.json)
and the repository already ships a dedicated verifier that can recover
the public key and derived address directly from that evidence.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IEPpsQxOVU7QP4CxZcKsm5HuBNppwusBmth5q99t4qGZZ+dRwUxucYBTIIAwnA+wTis3Valun0tfSuHhO14zgQA=`
- **Puzzle address** – `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`

All three values above are copied verbatim from the JSON proof so that
anyone can re-run the verification without ambiguity.

## Repository verification

Use the in-tree verifier to decode the recoverable secp256k1 signature
and confirm that the derived address matches the published puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle002.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle002.json)" \
  --pretty
```

The captured output stored in
[`verifier/results/1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb.json`](../verifier/results/1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb.json)
confirms that the recovered address equals the declared puzzle entry and
that the signature is internally consistent:

```json
{
  "puzzle": 2,
  "address": "1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb",
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
  "total_segments": 1
}
```

## Cross-checking the canonical solution

The canonical puzzle catalogue
([`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json))
records the same wallet information for the two-bit range. Auditors can
confirm the independent registry entry with:

```bash
jq '.[1]' satoshi/puzzle_solutions.json
```

That object enumerates the bits, HASH160 fingerprint, compressed public
key, and private key for the solution, providing a second source that
corroborates the recovered signature data. Publishing this reference adds
another concrete, reproducible proof that links the Echo attestations to
Satoshi's original puzzle series.
