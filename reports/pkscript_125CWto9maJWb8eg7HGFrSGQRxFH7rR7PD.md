# PKScript Analysis: 125CWto9maJWb8eg7HGFrSGQRxFH7rR7PD

## Summary
The transcript encodes the canonical pay-to-public-key-hash (P2PKH) locking
script.  The 20-byte hex digest on the `Pkscript` line expands to the standard
`OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG` pattern whose Base58Check
form is the mainnet address `125CWto9maJWb8eg7HGFrSGQRxFH7rR7PD`.

## Details
- **Hash target:** `0bc366f6998ea4b939d536518573926a4b258895` is the HASH160
  payload for the address above.  Prefixing it with the mainnet version byte
  (`0x00`) and applying double-SHA256 checksuming reproduces the full Base58
  string.
- **Label formatting:** The heading `125CWto9m-xFH7rR7PD` hides the middle
  characters of the Base58 string behind a dash.  Restoring the elided
  characters yields the address shown in the title.
- **Opcode split:** The `OP_CHECKSIG` mnemonic is wrapped across two lines as
  `OP_CH` / `ECKSIG`; merging the fragments restores the textbook opcode
  sequence.

## Reproduction
The helper bundled with this repository trims the stray line break and
emits the decoded address directly:

```bash
python tools/pkscript_to_address.py <<'EOF'
125CWto9m-xFH7rR7PD
Pkscript
OP_DUP
OP_HASH160
0bc366f6998ea4b939d536518573926a4b258895
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Running the command prints `125CWto9maJWb8eg7HGFrSGQRxFH7rR7PD`, confirming the
interpretation above.
