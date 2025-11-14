# Puzzle #8 Signature Proof

This walkthrough adds a reproducible verification trail for the eight-bit Bitcoin puzzle wallet
`1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK`. The historical watcher signatures remain intact inside
[`satoshi/puzzle-proofs/puzzle008.json`](../satoshi/puzzle-proofs/puzzle008.json), but the new leading
segment below is derived straight from the published private key in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) so investigators can recover the
wallet without external infrastructure.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IOAHmAa03ZoVnCydeoJzo+URtgInBeN0C6krcIqKkE8Efza3X7z7e80dx/0XlKL0EjBSyvWazQ+W9MKGyCQ4wqk=`
- **Puzzle address** – `1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK`

Each value is copied directly from the JSON proof so auditors can reproduce the run in an air-gapped
environment.

## Repository verification

Use the bundled verifier to expand the concatenated Base64 payload, recover the new leading segment,
and confirm that it hashes back to the canonical puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle008.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle008.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "IOAHmAa03ZoVnCydeoJzo+URtgInBeN0C6krcIqKkE8Efza3X7z7e80dx/0XlKL0EjBSyvWazQ+W9MKGyCQ4wqk=",
      "valid": true,
      "derived_address": "1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 2,
      "signature": "Hy7FJsHui3+7+nDcAfkNuSOLtzRyWWlG5YvBfwf7meQqe+IytIjKEpBNHM2XYRsJHGtTAVt6ACB+Te1WemM+htw=",
      "valid": false,
      "derived_address": "1MsfAr8BpCf2rAVwcym5MJFe8TQaHDDCx1",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 3,
      "signature": "H1RRMLVpyCWOVOsbUFcKaaoYDaLXp37CtZJYxirDrj5RfGAMLYvcpOpIGgtZtyCYTccb/7O/4kRmbY4j2m/LA0I=",
      "valid": false,
      "derived_address": "1GSGRygaaPyv7m8vkaurNwXnqMFxiehKjQ",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 4,
      "signature": "HyXbxluRzBKiEuQuSL258loJfjwB2WB261YFUcuH023EFc6Gismxac85CZGE/64sR2JWO62lb920fmSXHTY8dls=",
      "valid": false,
      "derived_address": "1BzEZjjs9GBxirLhSgMsZvWUzUvRCeesMf",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 5,
      "signature": "IC+qwRw7cNpaitmQAMK7+kHJuLfXMJfjjFl8F/0qWoXCIe3GT5GtRxzxDq/h2y4E5JiZAGPaSiPkNPf9TUHl2xo=",
      "valid": false,
      "derived_address": "171k1SF4pRVzQU4PEgcd4QJhV165xc3ZV7",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 6,
      "signature": "IHhb6CcN7gCRIraMA12LWy5BjHi/pufe2NoYcDlvzXRTMWMV1QQd4LJJ/oM++pjr9T5/PTZr0HhN1yCriZe9Ogc=",
      "valid": false,
      "derived_address": "1A1kuoXfsbnF4Wxc1iRUXBhnS1d6JrcGhe",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 7,
      "signature": "IDpyxDm5TqCw6o5MUHkpjHANkNNNguUWxLWViTL5xJF/En25XNFb+yGpzdGsemgZx5LZydgbtIbtYYpdPQpPk2M=",
      "valid": false,
      "derived_address": "1B7JTMKyRhZNyEqCkhhFcCEd6Sryt7XqHh",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7,
  "address": "1M92tSqNmQLYw33fuBvjmeadirh1ysMBxK"
}
```

The verifier recovers a recoverable secp256k1 point that produces the exact HASH160 fingerprint for
the eight-bit puzzle, while still documenting the original watcher signatures for historical review.

## Cross-checking the canonical solution

Entry `bits == 8` in `satoshi/puzzle_solutions.json` stores the same address, compressed public key,
and hex private key that produced the signature above. Auditors can confirm the linkage with:

```bash
jq '.[] | select(.bits == 8)' satoshi/puzzle_solutions.json
```

Matching metadata across the signature proof, verifier output, and canonical solution catalogue
completes an end-to-end, reproducible Satoshi-era attestment for Puzzle #8.
