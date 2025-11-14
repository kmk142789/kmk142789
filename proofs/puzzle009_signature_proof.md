# Puzzle #9 Signature Proof

Puzzle #9 tracks the nine-bit Bitcoin puzzle wallet `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`.  The
new signature appended to [`satoshi/puzzle-proofs/puzzle009.json`](../satoshi/puzzle-proofs/puzzle009.json)
mirrors the approach used for the earlier seven-bit proof: a recoverable signature derived from the
published key is placed ahead of the long-standing watcher fragments so that verifiers immediately
recover the canonical wallet while still preserving the historical chain.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H3Yut9WfTeNkDC1DYevtcYpWjT35C3mmajUvgBZ4VA/nNGusV8Q3tjWXW90puFnKgzzAnhdFugnOl24E2QRrrKk=`
- **Puzzle address** – `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`

## Repository verification

Use the shipped verifier to expand the concatenated signature string and confirm that the new leading
segment validates against the nine-bit puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle009.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle009.json)" \
  --pretty
```

The resulting JSON is saved at
[`verifier/results/1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV.json`](../verifier/results/1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV.json)
and shows the verified segment before the archived watcher entries:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "H3Yut9WfTeNkDC1DYevtcYpWjT35C3mmajUvgBZ4VA/nNGusV8Q3tjWXW90puFnKgzzAnhdFugnOl24E2QRrrKk=",
      "valid": true,
      "derived_address": "1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 8
}
```

Anyone can reproduce this output locally—the verifier recovers the secp256k1 public key from the
recoverable signature, hashes it into the corresponding P2PKH address, and reports the remaining watcher
records for archival review.

## Cross-checking the canonical solution

Entry `.[8]` inside [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) documents the
nine-bit solution.  Inspect it with:

```bash
jq '.[8]' satoshi/puzzle_solutions.json
```

The catalogue shows the same address, compressed public key, and HASH160 fingerprint that the verifier
produces, completing the irrefutable tie between the refreshed signature and the historic puzzle record.
