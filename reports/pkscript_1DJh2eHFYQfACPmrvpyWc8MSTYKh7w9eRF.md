# PKScript Analysis: 1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF

## Summary
The provided locking script is the canonical pay-to-public-key-hash (P2PKH) template. It duplicates the top stack item, hashes it with `OP_HASH160`, enforces equality against the embedded 20-byte hash via `OP_EQUALVERIFY`, and finally validates a signature with `OP_CHECKSIG`. As with other puzzles, splitting `OP_CHECKSIG` across the `OP_CH` / `ECKSIG` lines is purely a formatting artefact; the opcode is reconstructed before evaluation, leaving the semantics unchanged.

```
OP_DUP
OP_HASH160
86f9fea5cdecf033161dd2f8f8560768ae0a6d14
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Hash payload:** `86f9fea5cdecf033161dd2f8f8560768ae0a6d14` is a 20-byte RIPEMD-160 digest, exactly matching the length required for P2PKH redemption.
- **Derived address:** Prefixing the hash with the Bitcoin mainnet version byte (`0x00`), appending the Base58Check checksum, and encoding yields the wallet address `1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF`.
- **Opcode integrity:** Normalisation merges the split `OP_CH` / `ECKSIG` tokens back into `OP_CHECKSIG`, confirming the script is a valid five-opcode P2PKH sequence.

## Reproduction
The result can be reproduced with the repository helper script:

```
python tools/pkscript_to_address.py <<'EOF'
1DJh2eHFY-YKh7w9eRF
Pkscript
OP_DUP
OP_HASH160
86f9fea5cdecf033161dd2f8f8560768ae0a6d14
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Running the helper emits the canonical address `1DJh2eHFYQfACPmrvpyWc8MSTYKh7w9eRF`, matching the derivation described above.
