# PKScript Analysis: 1EcSu4ucxUpMgbWerA8jwfre8FigEvoZ15

## Summary
The transcript encodes a legacy pay-to-public-key (P2PK) locking script. It
pushes a full 65-byte uncompressed secp256k1 public key onto the stack and ends
with `OP_CHECKSIG`, meaning any spend must provide a signature that validates
directly against the embedded key.

## Details
- **Public key (hex):** `045793aa1d737d8be6b6fbce8d78df2cf115d4424f38ec07c95ef7766be82a1a3f546db2cd13fd6dab2e077b8ec35af4e2c718724b919e550927555758870be235`
- **Script (ASM):** `045793aa1d737d8be6b6fbce8d78df2cf115d4424f38ec07c95ef7766be82a1a3f546db2cd13fd6dab2e077b8ec35af4e2c718724b919e550927555758870be235 OP_CHECKSIG`
- **Pubkey hash160:** `954dcfeaa324011fc7a746ee0291d7b14ae188e8`
- **Derived P2PKH address:** `1EcSu4ucxUpMgbWerA8jwfre8FigEvoZ15`
- **Fragment restoration:** The clue string `1EcSu4ucx-FigEvoZ15` keeps the
  first nine and last ten Base58 characters, replacing the missing middle
  section with a hyphen. Reinserting the omitted substring `UpMgbWerA8jwfre8`
  yields the full address above.

## Reproduction
Use the repository helper to decode the transcript and restore the redacted
address:

```bash
python tools/pkscript_to_address.py <<'EOF_SNIPPET'
1EcSu4ucx-FigEvoZ15
Pkscript
045793aa1d737d8be6b6fbce8d78df2cf115d4424f38ec07c95ef7766be82a1a3f546db2cd13fd6dab2e077b8ec35af4e2c718724b919e550927555758870be235
OP_CHECKSIG
EOF_SNIPPET
```

The helper prints `1EcSu4ucxUpMgbWerA8jwfre8FigEvoZ15`, confirming that the
embedded public key hashes to the recovered address.
