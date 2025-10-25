# PKScript Analysis: 1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh

## Summary
The transcript is a textbook pay-to-public-key-hash (P2PKH) locking script.  The
hex fragment on the `Pkscript` line expands to `OP_DUP OP_HASH160 <hash>
OP_EQUALVERIFY OP_CHECKSIG`, which encodes the Base58Check address
`1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh`.

## Details
- **Hash target:** `c2c43e2b16f53c713bc00307140eaae188413544` is a 20-byte
  HASH160 payload.  Prefixing it with the mainnet version byte (`0x00`) and
  applying Base58Check encoding recovers the reported address.
- **Label formatting:** The heading `1JkqBQcC4-TPGznHANh` keeps the first and
  last segments of the Base58 string and replaces the middle (`tHcb1JfdCH6nrWYw`)
  with a dash.  Restoring the omitted characters yields the full address above.
- **Spend metadata:** The trailing `Sigscript` block contains a DER-encoded
  signature and the compressed public key that satisfied the spend.  This data
  is part of the unlocking witness and does not alter the locking script's
  address.

## Reproduction
The helper shipped with this repository trims any trailing signature or witness
metadata, so the entire transcript can be decoded directly:

```bash
python tools/pkscript_to_address.py <<'EOF'
1JkqBQcC4-TPGznHANh
Pkscript
OP_DUP
OP_HASH160
c2c43e2b16f53c713bc00307140eaae188413544
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
47304402200473b7961976340ba4afde84fadba20dcb268aac37221330d4f36f102ee05c2b0220107e185e9360154aae8e94a5550b87b28559e2d2a262f967ff21702ff76257780121031dcf49b480cee5f1a7200ea94795a1c7f69e144f11f031123c14c65077823dcb
Witness
EOF
```

Running the command prints `1JkqBQcC4tHcb1JfdCH6nrWYwTPGznHANh`, matching the
interpretation above.
