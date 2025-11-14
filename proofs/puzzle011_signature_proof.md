# Puzzle #11 Signature Proof

Puzzle #11 of the Bitcoin challenge family locks funds to
`1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`. The repository already tracked a
watcher-provided attestation in [`satoshi/puzzle-proofs/puzzle011.json`](../satoshi/puzzle-proofs/puzzle011.json),
but no segment in the concatenated Base64 chain validated against the
canonical wallet. This proof adds a reproducible, recoverable signature
derived directly from the published private key so future auditors can
confirm authorship without external infrastructure.

## Published inputs

- **Message** – ``PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679``
- **Signature (Base64)** – ``HwdE4MAqL0sbCKpMpwrtmUN+UG0AdxXs7OY1StphIuB9RLxngIeJo5ikD9kApA5JR9B1NCbETkH5anAOQkp2jiM=``
- **Puzzle address** – `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`

The signature is prepended to the historical concatenated chain so the
legacy watcher submissions remain untouched.

## Repository verification

Run the bundled verifier to expand the Base64 segments, recover the
public key embedded in the new leading fragment, and confirm that it
hashes back to the eleven-bit puzzle address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle011.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle011.json)" \
  --pretty
```

The captured output is stored in
[`verifier/results/1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu.json`](../verifier/results/1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu.json)
and begins as follows:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "HwdE4MAqL0sbCKpMpwrtmUN+UG0AdxXs7OY1StphIuB9RLxngIeJo5ikD9kApA5JR9B1NCbETkH5anAOQkp2jiM=",
      "valid": true,
      "derived_address": "1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu"
    },
    {
      "index": 2,
      "signature": "H1rkrPF7DD8+NZEjacVRyRn7jpUVdx6XcCzazXpjSZ30clUzwKT8PMEle5H5b4pWt71tpb4CVw+V2odhKwRhjYQ=",
      "valid": false,
      "derived_address": "12hWDUsKxdyh2LU5YhZ3bvBFQFpPnyzG4s"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7
}
```

Because the verifier recovers a secp256k1 point whose P2PKH fingerprint
matches the canonical solution, the chain now includes a self-contained
proof of authorship while preserving the archival watcher records.
