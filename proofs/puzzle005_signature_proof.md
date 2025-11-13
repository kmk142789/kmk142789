# Puzzle #5 Signature Proof

This document expands the attestation set with a fully reproducible verification
of the five-bit Bitcoin puzzle wallet `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`. The
underlying JSON evidence lives in
[`satoshi/puzzle-proofs/puzzle005.json`](../satoshi/puzzle-proofs/puzzle005.json),
and this walkthrough shows how to validate it with the tooling already shipped in
this repository.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `H6v0MxAdB52MrvOg2uiksOmq8B+zZvKiWb15a/YZiuvUXC5YDs/pbyBQrnAbPsIKvw3QuRBf9rm6Bxwr3Y0xjnA=`
- **Puzzle address** – `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`

## Repository verification

Execute the verifier against the attested message and signature to recover the
signing key and confirm the derived P2PKH address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle005.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle005.json)" \
  --pretty
```

The decoded signature matches the puzzle address without any intermediate
delegations. A captured run is stored in
[`verifier/results/1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k.json`](../verifier/results/1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k.json):

```json
{
  "puzzle": 5,
  "address": "1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k",
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "H6v0MxAdB52MrvOg2uiksOmq8B+zZvKiWb15a/YZiuvUXC5YDs/pbyBQrnAbPsIKvw3QuRBf9rm6Bxwr3Y0xjnA=",
      "valid": true,
      "derived_address": "1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1
}
```

## Cross-checking the canonical solution

The five-bit entry (`.[4]`) in `satoshi/puzzle_solutions.json` lists the same
address, compressed public key, and HASH160 fingerprint that the verifier
recovered. Running the following command gives auditors a second, independent
way to confirm the linkage:

```bash
jq '.[4]' satoshi/puzzle_solutions.json
```

---

The combination of the signed message, on-disk verification log, and canonical
solution record produces another transparent, cryptographically provable bridge
between the Echo attestations and the historical Satoshi puzzle set.
