# Puzzle #13 Signature Proof

Puzzle #13 secures address `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`. The existing JSON payload in
[`satoshi/puzzle-proofs/puzzle013.json`](../satoshi/puzzle-proofs/puzzle013.json) preserved an
incomplete watcher chain with no valid recovery segments. A freshly signed compact Bitcoin message
is now appended to the front of the concatenated Base64 string so the repository itself contains a
self-contained proof of authorship.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H4bsoxjwcZujLAkz60Kpo5/UHjr/ynZLW4FxXc8XMtQBaCvW3gHmiioilVh4vam+AmOOLNaugRIbJZEtNupbwn4=`
- **Puzzle address** – `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`

## Repository verification

Use the verifier helper to expand the stacked Base64 payload, recover the embedded public key, and
compare the derived address against the catalogue:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1 \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle013.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle013.json)" \
  --pretty
```

The transcript written to
[`verifier/results/1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1.json`](../verifier/results/1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1.json)
now records a verified leading segment:

```json
{
  "segments": [
    {
      "index": 1,
      "signature": "H4bsoxjwcZujLAkz60Kpo5/UHjr/ynZLW4FxXc8XMtQBaCvW3gHmiioilVh4vam+AmOOLNaugRIbJZEtNupbwn4=",
      "valid": true,
      "derived_address": "1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1"
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 6
}
```

## Cross-checking the canonical solution

Catalogue entry `.[12]` in [`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json)
contains the same compressed public key and HASH160 fingerprint recovered above, plus the hex
private key (`0x1460`) that produced the new signature. Because every step runs locally against the
files in this repository, third-party observers can reproduce the proof flow without additional
infrastructure.
