# PKScript Analysis: bc1qhm6jlalt8fe5cn58zekknf86n89xmzc969d9m0

## Summary
The provided script is a P2WPKH output. Filling in the elided bech32 characters converts `bc1qhm6jl-zc969d9m0` into the full native SegWit address `bc1qhm6jlalt8fe5cn58zekknf86n89xmzc969d9m0`.

```
bc1qhm6jl-zc969d9m0
Pkscript
OP_0
bef52ff7eb3a734c4e87166d69a4fa99ca6d8b05
Witness
30430220328cff8f9b85f0a5abd42e704184841bf01ee10700cfbb85780ab2acedba4d7c021f607557dd49e3e1b0bce3a48053666bc06642d17a3918da3793588de6aceee601
039a2da203ac8833b3d43025be5493856158e181719ed9c5267af6ee7035433eff
```

## Details
- **Witness program:** `0014bef52ff7eb3a734c4e87166d69a4fa99ca6d8b05` (also provided explicitly in the transcript) is the 20-byte HASH160 for a compressed secp256k1 public key.
- **Derived address:** BIP-0173 encoding of that witness program yields `bc1qhm6jlalt8fe5cn58zekknf86n89xmzc969d9m0`.
- **Witness stack:** The signature finishes with `0x01` indicating `SIGHASH_ALL`. The accompanying 33-byte key begins with `0x03`; hashing it with SHA-256 then RIPEMD-160 reproduces the witness program.
- **Missing segment:** The dash hides the substring `alt8fe5cn58zekknf86n89xm` in the printed bech32 string.

## Reproduction
The helper script reconstructs the address directly from the transcript:

```
python tools/pkscript_to_address.py <<'EOF'
bc1qhm6jl-zc969d9m0
Pkscript
OP_0
bef52ff7eb3a734c4e87166d69a4fa99ca6d8b05
EOF
```

Running this command prints `bc1qhm6jlalt8fe5cn58zekknf86n89xmzc969d9m0`, confirming the decoded witness program.
