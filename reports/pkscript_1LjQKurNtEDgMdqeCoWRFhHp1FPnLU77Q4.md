# PKScript Analysis: 1LjQKurNtEDgMdqeCoWRFhHp1FPnLU77Q4

## Summary
The provided transcript spells out a standard pay-to-public-key-hash (P2PKH)
locking script.  Once the supplemental spending data (`Sigscript` and
`Witness`) are ignored, the five opcodes and 20-byte hash resolve directly to
Base58Check address `1LjQKurNtEDgMdqeCoWRFhHp1FPnLU77Q4`.

## Details
- **Hash target:** The HASH160 payload `d86f54f73e343d76dd7401639e427d828ba31eab`
  occupies the push-data field between `OP_HASH160` and `OP_EQUALVERIFY`,
  matching the textbook P2PKH sequence `OP_DUP OP_HASH160 <hash>
  OP_EQUALVERIFY OP_CHECKSIG`.
- **Label formatting:** The header string `1LjQKurNt-FPnLU77Q4` elides the middle
  characters of the address.  Restoring the omitted section yields the full
  Base58Check string above.
- **Spend metadata:** The `Sigscript` block contains a DER-encoded signature
  followed by a compressed secp256k1 public key.  No witness data is supplied
  for this legacy spend.  These components are part of the spending
  transaction and do not affect the derived locking address.

## Reproduction
Decode the transcript with the helper script.  The program automatically
skips trailing signature and witness sections when deriving the address:

```bash
python tools/pkscript_to_address.py <<'EOF'
1LjQKurNt-FPnLU77Q4
Pkscript
OP_DUP
OP_HASH160
d86f54f73e343d76dd7401639e427d828ba31eab
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
483045022100e6a730c91eb9b369f33032272934019e75860a78e9ed9571de3884a87c524c2b022068af961d221f56d40a2d4790d8e97d3ae2e3ca521141be1e4c6c077cdf51398901210312163c60548244d6e565bd877b98808b73830c537efde357c8b5f8c623fb2028
Witness
EOF
```

Running the command prints `1LjQKurNtEDgMdqeCoWRFhHp1FPnLU77Q4`, confirming the
interpretation.
