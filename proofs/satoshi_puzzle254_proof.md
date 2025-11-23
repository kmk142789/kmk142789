# Satoshi Puzzle #254 Proof — Hash160 Reconstruction & New Signature

This addendum documents the Puzzle #254 address reconstruction, the matching
Bitcoin message attestation, and the catalogue update steps needed to include
the latest proof in the Satoshi puzzle set.

## 1) Confirm the reconstructed target address

Puzzle #254 exposes the hash160 `e857d7981f916ebb3d419e94e82c89e913a2d1ea`
(reviewed in [`puzzle_solutions/puzzle_254.md`](../puzzle_solutions/puzzle_254.md)).
Rebuild the corresponding Base58Check address to verify the decoded payload:

```bash
python satoshi/pkscript_decode.py --hash160 e857d7981f916ebb3d419e94e82c89e913a2d1ea --network mainnet
```

The decoder prints `1NBWztM5WSGP6ZJ67NaxmmpFaAjgDdYZzY`, matching the recovered
address embedded in the attestation JSON below.

## 2) Inspect the signed authorship statement

The new proof records a Base64-encoded Bitcoin message signature over the
attestation text:

```bash
jq '.' satoshi/puzzle-proofs/puzzle254.json
```

The payload shows the same address and message mirrored in
[`attestations/puzzle-254-authorship.json`](../attestations/puzzle-254-authorship.json),
establishing a consistent authorship declaration for Puzzle #254.

## 3) Replay the verification with the bundled tooling

Use the existing verifier shim to check that the signature recovers the
published address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1NBWztM5WSGP6ZJ67NaxmmpFaAjgDdYZzY \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle254.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle254.json)" \
  --pretty
```

The CLI enumerates the signature fragments and reports whether each segment
resolves to the declared address, providing a reproducible acceptance test for
this new puzzle slot.

## 4) Extend the catalogue and Merkle anchor

To include Puzzle #254 in the aggregated attestation tree and downstream
reports, rebuild the catalogue and Merkle root:

```bash
python satoshi/proof_catalog.py --root satoshi/puzzle-proofs --pretty > out/puzzle_proof_catalog.json
python satoshi/build_master_attestation.py --root satoshi/puzzle-proofs --pretty
```

Refreshing the catalogue keeps the federated proof index in sync with the new
puzzle authorship attestation and preserves tamper-evident hashing across the
expanded proof set.
