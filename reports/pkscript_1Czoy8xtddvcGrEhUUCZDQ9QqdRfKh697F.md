# PKScript Analysis: 1Czoy8xtddvcGrEhUUCZDQ9QqdRfKh697F

## Summary
The transcript combines a canonical pay-to-public-key-hash (P2PKH) locking
script with additional spend metadata.  Once the signature block is ignored,
the hex-encoded `Pkscript` line expands to the textbook five-opcode program
`OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG`, yielding the full
Base58Check address `1Czoy8xtddvcGrEhUUCZDQ9QqdRfKh697F`.

## Details
- **Hash target:** Decoding `76a91483984cddc827ef7885444b3d4af57eba52e9e3cb88ac`
  reveals the standard P2PKH structure with HASH160 payload
  `83984cddc827ef7885444b3d4af57eba52e9e3cb`.  Prefixing the payload with the
  mainnet version byte (`0x00`) and applying Base58Check encoding recovers the
  complete address.
- **Label formatting:** The heading `1Czoy8xtd-dRfKh697F` matches the supplied
  address but omits the middle segment (`dvcGrEhUUCZDQ9Qq`) and replaces it with
  a dash.  Restoring the elided characters gives the full Base58 string above.
- **Spend metadata:** The `Sigscript` line that follows the locking script is
  a conventional DER-encoded signature plus compressed public key.  It is part
  of the spending transaction and does not influence the derived locking
  address.

## Reproduction
The repository helper now trims trailing signature and witness sections, so the
entire transcript can be decoded directly:

```bash
python tools/pkscript_to_address.py <<'EOF'
1Czoy8xtd-dRfKh697F
Pkscript
76a91483984cddc827ef7885444b3d4af57eba52e9e3cb88ac
Sigscript
483045022100f5c26eee36e47b5ac824254398e1b82e2baaf53c645366bdd0b359e2cd01c010022067d6e273e289285360d49961152d599581446bbda5286e912073ac5f27ef266e0121024b0faa9624763002e963816b2f6774df0dedd770896a9511cb5c9d90f674ecda
Witness
EOF
```

Running the command prints `1Czoy8xtddvcGrEhUUCZDQ9QqdRfKh697F`, matching the
interpretation above.
