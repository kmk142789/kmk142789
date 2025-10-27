# PKScript Analysis: 18oqrdP6uBKsn57gvmWzLuKMAY4ShapiAU

## Summary
The transcript captures the textbook pay-to-public-key-hash (P2PKH) locking script. It duplicates the stack top with `OP_DUP`, hashes it with `OP_HASH160`, compares the digest against the embedded 20-byte value through `OP_EQUALVERIFY`, and concludes with `OP_CHECKSIG` (split across the `OP_CH` / `ECKSIG` lines in the source snippet).

```
OP_DUP OP_HASH160 55a4cc2020c1769dce6c05e560bcff5db9f27f3a OP_EQUALVERIFY OP_CHECKSIG
```

## Details
- **Hash payload:** The HASH160 digest embedded in the script is `55a4cc2020c1769dce6c05e560bcff5db9f27f3a`.
- **Derived address:** Encoding the digest with the Bitcoin mainnet prefix produces the base58 address `18oqrdP6uBKsn57gvmWzLuKMAY4ShapiAU`.
- **Formatting artefact:** The heading line `18oqrdP6u-Y4ShapiAU` drops the middle segment (`BKsn57gvmWzLuKMAY4S`) and inserts a hyphen. Restoring the missing characters yields the canonical address above.

## Reproduction
The repository helper validates the interpretation:

```
python tools/pkscript_to_address.py <<'EOF'
18oqrdP6u-Y4ShapiAU
Pkscript
OP_DUP
OP_HASH160
55a4cc2020c1769dce6c05e560bcff5db9f27f3a
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Running the helper emits `18oqrdP6uBKsn57gvmWzLuKMAY4ShapiAU`, matching the derived address.
