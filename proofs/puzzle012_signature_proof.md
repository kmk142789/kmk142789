# Puzzle #12 Signature Proof

Puzzle #12 controls the wallet `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`. Earlier submissions
stored in [`satoshi/puzzle-proofs/puzzle012.json`](../satoshi/puzzle-proofs/puzzle012.json)
were watcher relays that failed to verify against the canonical 12-bit address. This update
prepends a fresh recoverable signature generated directly from the published private key so
future auditors can replay the attestation offline without trusting external servers.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IFezeW/KYQOlGUe9xIdt+SZXf3mYcMWAGtiO8Ti10joaSyFNI+b8nVH4tlqF8sKhDSU8esgYBz7F8CXtyvb4bHo=`
- **Puzzle address** – `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`

The signature is concatenated ahead of the historic watcher stack to preserve provenance while
exposing a validated segment for the canonical wallet.

## Repository verification

Re-run the bundled verifier to recover the embedded secp256k1 public key and confirm the derived
P2PKH address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle012.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle012.json)" \
  --pretty
```

The captured transcript in
[`verifier/results/1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot.json`](../verifier/results/1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot.json)
now begins with a validated segment:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "IFezeW/KYQOlGUe9xIdt+SZXf3mYcMWAGtiO8Ti10joaSyFNI+b8nVH4tlqF8sKhDSU8esgYBz7F8CXtyvb4bHo=",
      "valid": true,
      "derived_address": "1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7
}
```

Every subsequent watcher submission remains recorded as invalid, preserving the audit trail while
anchoring the first segment to the canonical wallet.

## Cross-checking the canonical solution

Entry `.[11]` inside [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) stores the
12-bit puzzle metadata: the same HASH160 fingerprint, compressed public key, and private key
(`0xA7B`) used to mint the new signature. Because the recovered public key matches the catalogue,
anyone can reproduce the proof chain offline with only the JSON artefacts committed here.
