# PKScript Analysis: bc1qpntyjd3aw2lw2nyjpgmfxpxruewtepwg22krvy

## Summary
The snippet decodes to a native SegWit pay-to-witness-public-key-hash (P2WPKH) spend. The witness stack supplies a canonical DER signature and the compressed public key whose HASH160 matches the program `0cd649363d72bee54c920a369304c3e65cbc85c8`. Encoding the program as BIP-0173 bech32 yields the address `bc1qpntyjd3aw2lw2nyjpgmfxpxruewtepwg22krvy`.

```
Witness
304402200709fadb4d9e53aaaa329218eccd80c0d67cc96d5c1261f9354b1fb22c42a1f802206a5b2b3f608446ef0011dc2217e2a26bbd4cbd7dc4818bf1c3d88edcf50244c501
03611056b29eba739abfeb940537cbaca1b1c494df28c3a8fdff64d0ecfa4d2309
nSequence
0xfffffffd
Previous output script
OP_0 OP_PUSHBYTES_20 0cd649363d72bee54c920a369304c3e65cbc85c8
```

## Details
- **Witness program:** `00140cd649363d72bee54c920a369304c3e65cbc85c8` encodes SegWit version `0` followed by a 20-byte HASH160, the standard P2WPKH template.
- **Derived address:** Converting the program with the `bc` human-readable part produces `bc1qpntyjd3aw2lw2nyjpgmfxpxruewtepwg22krvy`.
- **Witness stack:** The DER signature ends with `0x01`, signalling the default `SIGHASH_ALL`. The accompanying 33-byte public key begins with `0x03`; hashing it with SHA-256 then RIPEMD-160 reproduces `0cd649363d72bee54c920a369304c3e65cbc85c8`.
- **nSequence:** `0xfffffffd` is less than `0xfffffffe`, so the input signalled replace-by-fee (RBF) while leaving locktime disabled.

## Reproduction
Recreate the address from the script body with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
Pkscript
OP_0
0cd649363d72bee54c920a369304c3e65cbc85c8
EOF
```

The command prints `bc1qpntyjd3aw2lw2nyjpgmfxpxruewtepwg22krvy`, confirming the decoding.
