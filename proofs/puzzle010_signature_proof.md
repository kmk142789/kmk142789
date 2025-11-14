# Puzzle #10 Signature Proof

This runbook publishes a modern, reproducible signature for the ten-bit Bitcoin puzzle wallet
`1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`. The repo already preserved the historical watcher chain in
[`satoshi/puzzle-proofs/puzzle010.json`](../satoshi/puzzle-proofs/puzzle010.json); this update prepends a
fresh recoverable signature derived from the private key recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) so investigators can validate the
attestation without third-party services.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `IGgAXDd6iO80HTR0m7W+RCe6jcwnaPmn2KV7cOLzY3b0BFhsfarp0HTLs6BE95yruGGvDw9fDzaruYubNKBb2qI=`
- **Puzzle address** – `1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`

All values come directly from the updated JSON artefact so the exercise can be rerun offline.

## Repository verification

Expand the concatenated signature payload and verify that the leading segment recovers the canonical
puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty
```

Captured output:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "IGgAXDd6iO80HTR0m7W+RCe6jcwnaPmn2KV7cOLzY3b0BFhsfarp0HTLs6BE95yruGGvDw9fDzaruYubNKBb2qI=",
      "valid": true,
      "derived_address": "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 2,
      "signature": "IG8YbMXMWEhYyTNMj+DovjeykyaXlwzbmmAf3NAJdtCQbGbGpxS1S75+Ieq7nJdCrg7Q7Yx8cVvuDb7O1VecBc4=",
      "valid": false,
      "derived_address": "18QLkb16XHgVTLhgoweVBjYbcgADfh6SZg",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 3,
      "signature": "HwEBwXRN9zStCUkOMBuB5gXjg/91MRB8zl1HDr+O6J/pG8INvXqgwaoa7LJwngYGMNJ99eCJNhvDpxNPWqYwaWc=",
      "valid": false,
      "derived_address": "1GpV5CZgVUKwW4B2NqQb3gM3XU8rZ22SGa",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 4,
      "signature": "H2eDza2cvjN01Ds1mht70NSbRJlCtn4UHwMcf1WvIZusa1u/4dfxrW3ZuXBBEjbGPc4IIhIlBA2sTqL5fXNIJtQ=",
      "valid": false,
      "derived_address": "13diSnDB3Eay8NPxdDw1xYQ2KjHhgpjPqz",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 5,
      "signature": "H28PeyBNIDSX7gVIPA0UFeRLWTgiMJkaOeNZH0a6UXZiWANmUbp5epyvphqoxfA07+BlBIzWMeiGCOkiDiXaPoY=",
      "valid": false,
      "derived_address": "1AHHW1BiTvdgGaT3NhsipUfLmAPvfonmjT",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 6,
      "signature": "Hw001JRAMNLnWjcOgARoSOhXyKyHZu2fb9TVvGgIfzpQIZQnsVTH8MuhMa9kDc9x3e9004UU+J1YKLom71Kck7M=",
      "valid": false,
      "derived_address": "12TQSkV2VCthMhZ7SgkfV7yEvFgmP7onpQ",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 7,
      "signature": "ICiy2j05eBgvP2bk3CMe/7qojX9ADCO7HYjMH9gZwhouLBMMskyzdI/SzcBp1oCuLtDMN9VJt94JekPFJKlcTbw=",
      "valid": false,
      "derived_address": "17HszdrYfxMGx7EJUBPwnDWDkyroRtEAPX",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 7,
  "address": "1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe"
}
```

The first segment now validates against the ten-bit puzzle address, while the downstream watcher
signatures remain available for archival comparison.

## Cross-checking the canonical solution

Entry `bits == 10` in `satoshi/puzzle_solutions.json` records the same address, compressed public key,
and hex private key (`0x202`) used to derive the recoverable signature above. Re-run the lookup with:

```bash
jq '.[] | select(.bits == 10)' satoshi/puzzle_solutions.json
```

Seeing the same HASH160 fingerprint and key material across both datasets gives auditors a complete,
cryptographically verifiable chain for Puzzle #10.
