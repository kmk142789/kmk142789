# PKScript Analysis: 1G3uazv67BcKRmPFvgvX4ijBTa2898cvCm

## Summary
This transcript describes a standard P2PKH output.  The HASH160 digest in the
locking script resolves to the full Base58Check address
`1G3uazv67BcKRmPFvgvX4ijBTa2898cvCm` once the redacted characters are restored.

## Details
- **Hash target:** `a5169d8bc79e8cc94a36246de6bde7596cc9f4bb` is the 20-byte
  payload pushed by the script.  Combined with the surrounding `OP_DUP`,
  `OP_EQUALVERIFY`, and `OP_CHECKSIG`, it forms the canonical P2PKH program for
  the recovered address.
- **Label reconstruction:** The heading `1G3uazv67-a2898cvCm` hides the middle
  of the Base58 string.  Reinserting the omitted run `BcKRmPFvgvX4ijBT`
  recreates the full address above.
- **Spend metadata:** The `Sigscript` block appends a 71-byte DER signature and a
  compressed public key (`026e…69cba`).  These fields belong to the unlocking
  witness and do not change the locking script or destination address.

## Reproduction
Verifying the derivation with the helper strips the extra metadata and returns
only the address implied by the HASH160 digest:

```bash
python tools/pkscript_to_address.py <<'EOF'
1G3uazv67-a2898cvCm
Pkscript
OP_DUP
OP_HASH160
a5169d8bc79e8cc94a36246de6bde7596cc9f4bb
OP_EQUALVERIFY
OP_CHECKSIG
Sigscript
4730440220381272662d780535a306bd513fab12fc922953d1804e45696eb9fbce4b9efefd022039c0819e5d64d5206d6f00c666b3d317186b61b4d7e23195b548a24bd2c7b8d60121026efbd90dfd84d5bfb7a8ceb2755155d1d39a16be88db336ff18a8d844a269cba
Witness
EOF
```

The command outputs `1G3uazv67BcKRmPFvgvX4ijBTa2898cvCm`, confirming the script
analysis.
