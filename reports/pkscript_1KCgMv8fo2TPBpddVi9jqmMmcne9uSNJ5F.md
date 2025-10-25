# PKScript Analysis: 1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F

## Summary
The supplied transcript spells out the canonical five-opcode
pay-to-public-key-hash (P2PKH) locking script.  Removing the
supplemental spending fields (`Sigscript` and the empty `Witness`
section) reveals the HASH160 fingerprint for mainnet address
`1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F`.

## Details
- **Hash target:** The push-data field between `OP_HASH160` and
  `OP_EQUALVERIFY` contains the 20-byte value
  `c7a7b23f6bd98b8aaf527beb724dda9460b1bc6e`.  Plugging that digest into
  the textbook P2PKH template `OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY
  OP_CHECKSIG` yields the familiar locking program for the address above.
- **Label reconstruction:** The first line, `1KCgMv8fo-ne9uSNJ5F`, hides
  the middle characters of the Base58Check address.  Restoring the
  missing segment `2TPBpddVi9jqmMmc` reproduces the full destination
  `1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F` that appears in the official
  Puzzle #100 solution catalogue.
- **Spend metadata:** The `Sigscript` block carries a DER-encoded
  signature followed by an uncompressed secp256k1 public key, which are
  specific to the spending transaction.  The witness section is empty,
  confirming this is a legacy (non-SegWit) spend.  Neither field alters
  the derived locking address.

## Reproduction
Derive the address locally with the helper utility.  The tool skips any
unlocking data that trails the locking script:

```bash
python tools/pkscript_to_address.py <<'EOF'
1KCgMv8fo-ne9uSNJ5F
Pkscript
OP_DUP
OP_HASH160
c7a7b23f6bd98b8aaf527beb724dda9460b1bc6e
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
47304402201476dc7ac901ead81908cadedc98b978d98c8901fb02f4e84699b71407ab562502207a6532157049e9319fcd5f2b407d33a1530f5166084572b747279792ab1bab23012103d2063d40402f030d4cc71331468827aa41a8a09bd6fd801ba77fb64f8e67e617
Witness
EOF
```

Running the command prints `1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F`,
confirming the interpretation of the provided transcript.
