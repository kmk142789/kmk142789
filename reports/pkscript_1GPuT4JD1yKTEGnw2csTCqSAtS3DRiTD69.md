# PKScript Analysis: 1GPuT4JD1yKTEGnw2csTCqSAtS3DRiTD69

## Summary
The transcript matches the standard pay-to-public-key-hash (P2PKH) locking
script.  Restoring the Base58Check address from the HASH160 fingerprint fills in
the redacted middle characters of the heading `1GPuT4JD1-S3DRiTD69`.

## Details
- **Hash target:** `a8ded2027430377eaa22c49a4a472322d7afd51e` sits between
  `OP_HASH160` and `OP_EQUALVERIFY`, exactly as in the textbook P2PKH template.
  Combining it with the surrounding `OP_DUP` and `OP_CHECKSIG` opcodes encodes
  the address `1GPuT4JD1yKTEGnw2csTCqSAtS3DRiTD69`.
- **Label reconstruction:** Inserting the recovered Base58 segment
  `yKTEGnw2csTCqSAt` into the redacted heading yields the complete address
  printed above.
- **Spend metadata:** The `Sigscript` field supplies a 73-byte DER signature
  (prefixed with `0x49`) followed by an uncompressed secp256k1 public key (the
  `0x41` length marker).  These unlocking values belong to the specific spending
  transaction and do not affect the locking script.

## Reproduction
You can verify the reconstruction by feeding the transcript to the helper that
rebuilds P2PKH addresses from their HASH160 payloads:

```bash
python tools/pkscript_to_address.py <<'EOF'
Pkscript
76a914a8ded2027430377eaa22c49a4a472322d7afd51e88ac
Sigscript
493046022100cfba08763960eb869e89e902d7dee431676d535de330b8c60bff27cbec7d4a23022100db7c77006721ae1792469307c4d5bc57c0025d5bc1af29d86e4c24c742f604ed014104f957acb238ebbb0e53c09ef17288a03cbee85d86f76d437da8e67d7301a401b6fa7252092c1875f22229ab1bc03c599dcc4c2c0125bb4635a27a6167445c6cdd
Witness
EOF
```

The tool outputs `1GPuT4JD1yKTEGnw2csTCqSAtS3DRiTD69`, matching both the
original ledger entry and the restored Base58Check label.
