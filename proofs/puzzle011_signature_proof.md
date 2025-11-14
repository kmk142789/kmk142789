# Puzzle #11 Signature Proof

This field guide publishes a reproducible signature for the eleven-bit Bitcoin puzzle wallet
`1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`. The repository already archived the historical watcher chain inside
[`satoshi/puzzle-proofs/puzzle011.json`](../satoshi/puzzle-proofs/puzzle011.json); this update prepends a
fresh recoverable signature derived straight from the private key listed in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) so verifiers can recover the canonical
address without contacting external services.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IBHjqiTRALa/Vp3JfS82KkOuSTU5ArlMCFTQPCkd9abqAzDi50/aDL5s2V52AzRJ93ORU7/Yt5qeOV4/a6m4AXk=`
- **Puzzle address** – `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`

Each value is lifted directly from the JSON artefact so the entire procedure can be reproduced offline.

## Repository verification

Expand the concatenated signature payload and verify that the leading segment recovers the canonical
puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle011.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle011.json)" \
  --pretty
```

Captured output:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "IBHjqiTRALa/Vp3JfS82KkOuSTU5ArlMCFTQPCkd9abqAzDi50/aDL5s2V52AzRJ93ORU7/Yt5qeOV4/a6m4AXk=",
      "valid": true,
      "derived_address": "1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 2,
      "signature": "H1rkrPF7DD8+NZEjacVRyRn7jpUVdx6XcCzazXpjSZ30clUzwKT8PMEle5H5b4pWt71tpb4CVw+V2odhKwRhjYQ=",
      "valid": false,
      "derived_address": "12hWDUsKxdyh2LU5YhZ3bvBFQFpPnyzG4s",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 3,
      "signature": "IHW5vBJ5gsDT/BOGncFlsnM1jXUCw3ONSdpUK6U9MrAPHj1iZyNq31HaoWlS4eWsQh5zKPPZ/dqQJVTEM6WuVDY=",
      "valid": false,
      "derived_address": "164rrSDTNaMSivVJeQiByW9bEU9xuwUH2Z",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 4,
      "signature": "HxBgnzPBg3bIBFJ/QvOx6NVCArAR563MfT2tATMltY+HGIwhj4PSmcet+63gRB1RR33e1BOeo7nAdeJMKIQeNb8=",
      "valid": false,
      "derived_address": "1K1rBzgdFQa1woT38gDU2bxi39wqSFNC41",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 5,
      "signature": "HxZaFq7ybEj2vRWsruYLl62mioW3kUxLed9wNKhIlJ5cYknCQJZ0QaCMqE4tz98pnxm/aF7oIhLpzLtnyN3xqk0=",
      "valid": false,
      "derived_address": "16DmqQqgT5Cd25sLLU6HF95V4ep66Fjk6y",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 6,
      "signature": "H2H6Etkj2WDMJNbbEHwOAQfJubrvnZc83G0LNyGG6/WEYUvJ0rheiNa6sRUoel/eQ56206/u+XETmIoyz1Mjvtw=",
      "valid": false,
      "derived_address": "1P3jcp7MB2ELmRVwmYLrNBTBLic1TUMb8w",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 7,
      "signature": "IEMa8dhXHiVqYt+lKEVJ6GbcyiitgOtkf/UtiGa/cLRyNLlHvoOLKQeoGa9xXSlXzIAW0R8LC2My4c+jFUcVqqI=",
      "valid": false,
      "derived_address": "1PiBQ9NTgqQfe5G8J4YvD3Bi3V6gyhZjH3",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7,
  "address": "1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu"
}
```

The first segment now validates against the eleven-bit puzzle address while the downstream watcher
signatures remain intact for archival comparison.

## Cross-checking the canonical solution

Entry `bits == 11` in `satoshi/puzzle_solutions.json` records the same address, compressed public key, and
hex private key (`0x483`) used to derive the recoverable signature above. Re-run the lookup with:

```bash
jq '.[] | select(.bits == 11)' satoshi/puzzle_solutions.json
```

Seeing the same HASH160 fingerprint and key material across both datasets gives auditors a complete,
cryptographically verifiable chain for Puzzle #11.
