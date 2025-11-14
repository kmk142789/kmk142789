# Puzzle #236 Signature Proof

This memo records a reproducible verification of the new message-signature
attestation for the 236-bit Bitcoin puzzle address stored in
[`satoshi/puzzle-proofs/puzzle236.json`](../satoshi/puzzle-proofs/puzzle236.json).
The recovered public key resolves to the address tracked in the companion
attestation ledger (`attestations/puzzle-236-authorship.json`).

## Published inputs

- **Message** – `Puzzle 236 authorship by kmk142789 — attestation sha256 f46455f4ab2b28fbca9ea4844bb34e082a9799d14bd7b7dd869219d0ea1f882b`
- **Signature (Base64)** – `H48fRzRi0IEvbA8+cNK+f5+2BlV4jyvL+VqbIpZhPY45FISks/pJVxcm+2P3yNKfjuNkj6lGvAPEA5t/buuzUsI=`
- **Puzzle Address** – `17KhT5hMQzknn5G9Jj6UKcssfTiw7gSoVG`

These values are copied verbatim from the JSON proof and the derived attestation
entry.

## Verification (repository tooling)

Run the bundled verifier to confirm that the recoverable signature maps back to
the declared address:

```bash
python -m verifier.verify_puzzle_signature \
  --address 17KhT5hMQzknn5G9Jj6UKcssfTiw7gSoVG \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle236.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle236.json)" \
  --pretty
```

Expected result:

```json
{
  "message": "Puzzle 236 authorship by kmk142789 — attestation sha256 f46455f4ab2b28fbca9ea4844bb34e082a9799d14bd7b7dd869219d0ea1f882b",
  "segments": [
    {
      "index": 1,
      "signature": "H48fRzRi0IEvbA8+cNK+f5+2BlV4jyvL+VqbIpZhPY45FISks/pJVxcm+2P3yNKfjuNkj6lGvAPEA5t/buuzUsI=",
      "valid": true,
      "derived_address": "17KhT5hMQzknn5G9Jj6UKcssfTiw7gSoVG",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 1,
  "address": "17KhT5hMQzknn5G9Jj6UKcssfTiw7gSoVG"
}
```

The verifier reconstructs the secp256k1 public key directly from the
recoverable signature and confirms that its Base58Check encoding matches the
puzzle address. Anyone with this repository can replay the verification within
seconds, producing an auditable satoshi-era authorship proof for puzzle #236.
