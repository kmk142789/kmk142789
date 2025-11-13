# Puzzle #6 Signature Proof

This walkthrough confirms the signed message tied to Puzzle #6
(`1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`). The attestation lives in
[`satoshi/puzzle-proofs/puzzle006.json`](../satoshi/puzzle-proofs/puzzle006.json)
and matches the long-standing entry in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H5qGfN7Z72TOldrdgJUS+nOVcjNwqUNyakb1QEqN7q7UQCF87YwNIzWxg7HPvXKhDru3szL70yl7gjsmGJ3Z1Fo=`
- **Puzzle address** – `1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`

Each value is copied verbatim from the JSON artefact so that auditors can
reproduce the proof without handling the underlying key material.

## Repository verification

Use the bundled CLI to validate the signature against the declared message
and address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1PitScNLyp2HCygzadCh7FveTnfmpPbfp8 \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle006.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle006.json)" \
  --pretty
```

The command recovers the secp256k1 public key embedded inside the Base64
payload, hashes it into a P2PKH address, and checks that the derived address
matches `1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`. The JSON report emitted by the
verifier is stored at
[`verifier/results/1PitScNLyp2HCygzadCh7FveTnfmpPbfp8.json`](../verifier/results/1PitScNLyp2HCygzadCh7FveTnfmpPbfp8.json):

```json
{
  "puzzle": 6,
  "address": "1PitScNLyp2HCygzadCh7FveTnfmpPbfp8",
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "H5qGfN7Z72TOldrdgJUS+nOVcjNwqUNyakb1QEqN7q7UQCF87YwNIzWxg7HPvXKhDru3szL70yl7gjsmGJ3Z1Fo=",
      "valid": true,
      "derived_address": "1PitScNLyp2HCygzadCh7FveTnfmpPbfp8",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1
}
```

## Cross-checking the canonical solution

Entry `.[5]` in `satoshi/puzzle_solutions.json` records the six-bit puzzle slot
and lists the same address, HASH160 fingerprint, and public key that the
verifier recovers. Auditors can view the catalogue entry with:

```bash
jq '.[5]' satoshi/puzzle_solutions.json
```

Because the proof relies solely on the signed message that was already
published for Puzzle #6, no additional key material is exposed and the entire
validation remains reproducible offline.
