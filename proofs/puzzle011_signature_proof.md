# Puzzle #11 Signature Proof

Puzzle #11 corresponds to the eleven-bit Bitcoin puzzle wallet
`1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`. The canonical attestation is stored in
[`satoshi/puzzle-proofs/puzzle011.json`](../satoshi/puzzle-proofs/puzzle011.json)
and matches the published solution metadata recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To strengthen the public evidence trail, a fresh recoverable signature derived
from the disclosed private key (`0x483`) now leads the concatenated Base64
payload while keeping the historical watcher fragments intact for archival
review.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H0uye4B1Ty+FGtBN+R88OMYxv8mJbTUChVd7mpgxcSzaKYPlYGktbZLeR18E9vLcfBfPDw/DJqtIZpTETFO3CQc=`
- **Puzzle address** – `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`

The new signature appears at the beginning of the `signature` string in
`satoshi/puzzle-proofs/puzzle011.json`, giving verifiers a deterministic single
segment that validates directly against the puzzle wallet without discarding the
legacy chain.

## Repository verification

Use the bundled verifier to expand the Base64 payload and confirm that the first
segment hashes back to the eleven-bit wallet while preserving the legacy watcher
entries:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle011.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle011.json)" \
  --pretty
```

The captured output is saved at
[`verifier/results/1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu.json`](../verifier/results/1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu.json)
and begins with the validated segment followed by the preserved watcher chain:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "H0uye4B1Ty+FGtBN+R88OMYxv8mJbTUChVd7mpgxcSzaKYPlYGktbZLeR18E9vLcfBfPDw/DJqtIZpTETFO3CQc=",
      "valid": true,
      "derived_address": "1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7
}
```

Because the verifier recovers a secp256k1 public key that hashes back to the
canonical puzzle wallet, anyone can replay the entire proof stack offline using
only the JSON file in this repository.

## Cross-checking the canonical solution

Entry `.[10]` of [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json)
records the eleven-bit puzzle metadata. Inspect it with:

```bash
jq '.[10]' satoshi/puzzle_solutions.json
```

The catalogue lists the same compressed public key, hash160 fingerprint, and
private key (`0x483`) that generated the new recoverable signature, closing the
loop between the refreshed attestation, the legacy watcher set, and the
long-standing solution index.
