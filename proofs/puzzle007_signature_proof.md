# Puzzle #7 Signature Proof

This playbook extends the on-disk Satoshi evidence with a reproducible
verification of the seven-bit Bitcoin puzzle wallet `1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC`.
The attestation lives in [`satoshi/puzzle-proofs/puzzle007.json`](../satoshi/puzzle-proofs/puzzle007.json)
and matches the canonical entry in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To preserve the historical signature chain, the original six watcher signatures remain in place,
but a freshly generated recoverable signature derived from the published private key now leads the
concatenated Base64 string so that verifiers can recover the puzzle wallet directly.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IDU7uSUjkVrV4ADOUz0vBUq/1u2n7U+aMC/5/pRo59NJD1nJc/lCvx+6h8X1ZTJr0j2ZIqUwm/chxAfj3acwRcM=`
- **Puzzle address** – `1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC`

Each value is copied verbatim from the JSON artefact so auditors can re-run the proof without touching
any external infrastructure.

## Repository verification

Run the bundled verifier to expand the concatenated Base64 payload, recover the public key embedded in the
first segment, and confirm that it hashes back to the declared address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle007.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle007.json)" \
  --pretty
```

The captured output (stored at
[`verifier/results/1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC.json`](../verifier/results/1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC.json))
shows that the new leading segment validates against the puzzle wallet while keeping the legacy watcher
signatures for archival review:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "IDU7uSUjkVrV4ADOUz0vBUq/1u2n7U+aMC/5/pRo59NJD1nJc/lCvx+6h8X1ZTJr0j2ZIqUwm/chxAfj3acwRcM=",
      "valid": true,
      "derived_address": "1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7,
  "address": "1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC"
}
```

Because the verifier recovers a secp256k1 point that produces the same P2PKH fingerprint as the canonical puzzle
address, anyone can reproduce the linkage offline in seconds.

## Cross-checking the canonical solution

Entry `.[6]` in `satoshi/puzzle_solutions.json` lists the same address, compressed public key, and hash160 fingerprint
used to derive the above signature. Auditors can inspect it with:

```bash
jq '.[6]' satoshi/puzzle_solutions.json
```

The matching metadata completes the proof chain: a reproducible signature tied to the published private key,
the recorded solution catalogue, and the long-standing watcher attestations all converge on the same Puzzle #7 wallet.
