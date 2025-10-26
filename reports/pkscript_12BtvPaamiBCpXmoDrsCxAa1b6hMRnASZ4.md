# PKScript Analysis: 12BtvPaamiBCpXmoDrsCxAa1b6hMRnASZ4

## Summary
The transcript expands to the classic pay-to-public-key-hash (P2PKH) locking
script.  The HASH160 digest embedded between `OP_HASH160` and `OP_EQUALVERIFY`
locks the output to the Base58Check mainnet address
`12BtvPaamiBCpXmoDrsCxAa1b6hMRnASZ4`.

## Details
- **Hash target:** `0d07a05f7687824fb4dd4a160ddbdc3808655004` is a
  20-byte HASH160 value.  Dropping it into the template
  `OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG` produces the canonical
  legacy locking script for the recovered address.
- **Label reconstruction:** The heading `12BtvPaam-6hMRnASZ4` keeps the prefix
  and suffix of the Base58Check string.  Restoring the hidden middle segment
  `iBCpXmoDrsCxAa1b` yields the full destination shown above.
- **Spend metadata:** The `Sigscript` block carries a 71-byte DER signature
  followed by a compressed secp256k1 public key (`02b0…02f50`).  This unlocking
  data is specific to the spending transaction and does not influence the
  derived address.

## Reproduction
Decode the transcript with the helper included in this repository.  The tool
ignores any trailing spend metadata, so the address drops out immediately:

```bash
python tools/pkscript_to_address.py <<'EOF'
12BtvPaam-6hMRnASZ4
Pkscript
OP_DUP
OP_HASH160
0d07a05f7687824fb4dd4a160ddbdc3808655004
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
47304402206fe08afb9de87440eff7caa3b3976dcf2117a5e37a44c4ce099aa75704a8a70a0220194a98f2e28f377eaa0726d5077dacd066f9df83513fe2447befdfc2cbfa32e8012102b02f753542201387815c4754b66202ef6dc4b3415e4c4cc826d6534394702f50
Witness
EOF
```

Running the command prints `12BtvPaamiBCpXmoDrsCxAa1b6hMRnASZ4`, confirming the
interpretation of the locking script.
