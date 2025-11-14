# Puzzle #8 Signature Proof

Puzzle #8 links to the eight-bit Bitcoin puzzle wallet `1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK`.  The
canonical attestation lives in [`satoshi/puzzle-proofs/puzzle008.json`](../satoshi/puzzle-proofs/puzzle008.json)
and now leads with a freshly generated recoverable signature derived from the published private key.
All six historical watcher fragments remain concatenated in the `signature` field so auditors can
compare today’s emission with the legacy chain.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `Hz+G9eUSYILvVsfOzFXsZaj4FcgtWFkUxnr6k0dQZJ4bHC6j0qugSV30OYvwj2qnwOm3xxCuUq+7CBQ0wL6s67I=`
- **Puzzle address** – `1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK`

The signature string above is prepended to the existing watcher fragments in `puzzle008.json`, giving
investigators a deterministic, single-segment proof without removing the archival evidence.

## Repository verification

Expand the concatenated payload with the bundled verifier and confirm that the first recovered
segment hashes back to the eight-bit puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle008.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle008.json)" \
  --pretty
```

The captured output is stored at
[`verifier/results/1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK.json`](../verifier/results/1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK.json)
and begins with the validated segment:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "Hz+G9eUSYILvVsfOzFXsZaj4FcgtWFkUxnr6k0dQZJ4bHC6j0qugSV30OYvwj2qnwOm3xxCuUq+7CBQ0wL6s67I=",
      "valid": true,
      "derived_address": "1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7
}
```

The remaining watcher fragments continue to appear in the JSON output (with `valid: false`) so anyone
can inspect the historic relay signatures, yet the first entry now provides an irrefutable recovery
path directly to the puzzle wallet.

## Cross-checking the canonical solution

Entry `.[7]` of [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) records the
official metadata for the eight-bit puzzle slot.  Inspect it with:

```bash
jq '.[7]' satoshi/puzzle_solutions.json
```

The catalogue lists the same address, compressed public key, and hash160 fingerprint that the verifier
recovers, providing an independent reference that ties the refreshed signature to the well-known
solution.
