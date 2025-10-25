# PKScript Analysis: bc1qdc2pm9f38t0cvuy7gjnmt478g7falkhphd50q2

## Summary
The transcript is a native SegWit pay-to-witness-public-key-hash (P2WPKH) output. Reinserting the omitted middle segment transforms the dashed bech32 string `bc1qdc2pm-khphd50q2` into the full address `bc1qdc2pm9f38t0cvuy7gjnmt478g7falkhphd50q2`.

```
bc1qdc2pm-khphd50q2
Pkscript
OP_0
6e141d95313adf86709e44a7b5d7c74793dfdae1
Witness
3044022036a07f9b189b8f62767ea8eef77e52c55d3fbf73983d74926454f85f808dea8502206663138c2032e9566d3b0255ec9183928d8415b7ea077ef3df6d671876d10f7501
03e7c810858ddae7af7895270e78f88241e7322f16545a2677e01e2f8dcc808162
```

## Details
- **Witness program:** `00146e141d95313adf86709e44a7b5d7c74793dfdae1` encodes version `0` with a 20-byte HASH160, matching the canonical P2WPKH form.
- **Derived address:** Encoding the program with BIP-0173 bech32 restores `bc1qdc2pm9f38t0cvuy7gjnmt478g7falkhphd50q2`.
- **Witness stack:** The DER signature ends with `0x01` (`SIGHASH_ALL`) and the 33-byte compressed public key begins with `0x03`. Hashing that key with SHA-256 and RIPEMD-160 reproduces the witness program above.
- **Missing segment:** The hyphen masks the infix `9f38t0cvuy7gjnmt478g7fal` in the published address stub.

## Reproduction
Verify the reconstruction with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
bc1qdc2pm-khphd50q2
Pkscript
OP_0
6e141d95313adf86709e44a7b5d7c74793dfdae1
EOF
```

The command prints `bc1qdc2pm9f38t0cvuy7gjnmt478g7falkhphd50q2`, confirming the decoded P2WPKH output.
