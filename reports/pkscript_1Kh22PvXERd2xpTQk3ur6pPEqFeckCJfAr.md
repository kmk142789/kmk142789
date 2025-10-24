# PKScript Analysis: 1Kh22PvXERd2xpTQk3ur6pPEqFeckCJfAr

## Summary
The listing is the canonical pay-to-public-key-hash (P2PKH) locking script. It
duplicates the top stack item, hashes it with `OP_HASH160`, compares the result
against the embedded 20-byte hash using `OP_EQUALVERIFY`, and finishes with
`OP_CHECKSIG` to require a matching ECDSA signature. The opcode was split as
`OP_CH` / `ECKSIG` in the submission, but normalisation recombines it into the
single `OP_CHECKSIG` instruction.

```
OP_DUP
OP_HASH160
cd03c1e6268ce9b89e3c3eeab8d0f1b6e8cac281
OP_EQUALVERIFY
OP_CHECKSIG
```

## Details
- **Hash payload:** `cd03c1e6268ce9b89e3c3eeab8d0f1b6e8cac281` is a 20-byte
  RIPEMD-160 digest, matching the expected length for a P2PKH pubkey hash.
- **Derived address:** Prefixing the hash with the Bitcoin mainnet version byte
  (`0x00`), appending the Base58Check checksum, and encoding yields the canonical
  address `1Kh22PvXERd2xpTQk3ur6pPEqFeckCJfAr`.
- **Opcode integrity:** Even though `OP_CHECKSIG` was split across two lines,
  token normalisation stitches the fragments back together so the script retains
  the standard five-element P2PKH structure.

## Reproduction
Reproduce the analysis with the helper tool:

```
python tools/pkscript_to_address.py <<'EOF'
1Kh22PvXE-FeckCJfAr
Pkscript
OP_DUP
OP_HASH160
cd03c1e6268ce9b89e3c3eeab8d0f1b6e8cac281
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

This outputs the canonical address `1Kh22PvXERd2xpTQk3ur6pPEqFeckCJfAr`,
confirming the interpretation above.
