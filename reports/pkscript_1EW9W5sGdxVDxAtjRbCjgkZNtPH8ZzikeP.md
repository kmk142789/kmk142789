# PKScript Analysis: 1EW9W5sGdxVDxAtjRbCjgkZNtPH8ZzikeP

## Summary
The locking script is the familiar P2PKH template.  Its HASH160 payload encodes
the address `1EW9W5sGdxVDxAtjRbCjgkZNtPH8ZzikeP` after the masked characters in
the label are restored.

## Details
- **Hash target:** `941ccb7383109b47b841044c9f865785676b0918` is the 20-byte
  HASH160 digest pushed by the script.  With `OP_DUP`, `OP_EQUALVERIFY`, and
  `OP_CHECKSIG` it forms the canonical P2PKH locking program for the recovered
  address.
- **Label reconstruction:** The first line `1EW9W5sGd-PH8ZzikeP` omits the middle
  run of the Base58 string.  Inserting the hidden segment `xVDxAtjRbCjgkZNt`
  recreates the full address.
- **Spend metadata:** The `Sigscript` section carries a 71-byte DER signature
  and a compressed secp256k1 public key (`03e5…97d61`).  These unlocking values
  describe the spend that consumed the output and do not modify the locking
  address.

## Reproduction
Use the helper utility to strip the supplemental metadata and rebuild the
Base58Check destination from the HASH160 payload:

```bash
python tools/pkscript_to_address.py <<'EOF'
1EW9W5sGd-PH8ZzikeP
Pkscript
OP_DUP
OP_HASH160
941ccb7383109b47b841044c9f865785676b0918
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
47304402206dd7886e2dd3551a051f370b1e2cca45ec30faac4e842c2125806d65855b37ae022018d75404e1559457f46c2c57d0387e4136a86f608a4239dcbae0e6c2fafea7dd012103e56c48f1bc4a6d06a2e0a4ad53c7674403dbfdaaeee3ecc86aff294b04997d61
Witness
EOF
```

The command prints `1EW9W5sGdxVDxAtjRbCjgkZNtPH8ZzikeP`, validating the
interpretation of the script.
