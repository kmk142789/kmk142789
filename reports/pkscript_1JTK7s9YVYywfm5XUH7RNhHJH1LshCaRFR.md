# PKScript Analysis: 1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR

## Summary
The provided locking script is the standard pay-to-public-key-hash (P2PKH) template. It duplicates the top stack item, hashes it with `OP_HASH160`, compares the result to the embedded 20-byte hash with `OP_EQUALVERIFY`, and then enforces signature verification with `OP_CHECKSIG`. The line break splitting `OP_CHECKSIG` into `OP_CH` / `ECKSIG` does not change the semantics—the opcode recombines during normalization.

```
OP_DUP
OP_HASH160
bf7413e8df4e7a34ce9dc13e2f2648783ec54adb
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Hash payload:** `bf7413e8df4e7a34ce9dc13e2f2648783ec54adb` is a 20-byte RIPEMD-160 hash (40 hexadecimal characters) as expected for a P2PKH script.
- **Derived address:** Prefixing the hash with the Bitcoin mainnet version byte (`0x00`), appending the Base58Check checksum, and encoding yields the canonical address `1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR`.
- **Opcode integrity:** Although the supplied text split `OP_CHECKSIG` across two lines, the decoder stitches opcode fragments back together before validation, confirming the script remains a valid five-element P2PKH sequence.

## Reproduction
The result can be reproduced with the repository helper tool:

```
python tools/pkscript_to_address.py <<'EOF'
1JTK7s9YV-1LshCaRFR
Pkscript
OP_DUP
OP_HASH160
bf7413e8df4e7a34ce9dc13e2f2648783ec54adb
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

This outputs the canonical address `1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR`, confirming the interpretation above.
