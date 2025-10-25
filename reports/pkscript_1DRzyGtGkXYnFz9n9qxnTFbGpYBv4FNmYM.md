# PKScript Analysis: 1DRzyGtGkXYnFz9n9qxnTFbGpYBv4FNmYM

## Summary
The final transcript is a P2PK output. Reinstating the omitted section turns `1DRzyGtGk-YBv4FNmYM` into the complete address `1DRzyGtGkXYnFz9n9qxnTFbGpYBv4FNmYM`.

```
1DRzyGtGk-YBv4FNmYM
Pkscript
04ad6f8b8c71859ab32eb863c88f33a9c6d621639cb1b6094ee61c7a8bdfa2fd7070c620d8f0f99e98b090ce932a7ea8d7595eadd0d80ce966c52bece59b96c88f
OP_CHECKSIG
```

## Details
- **Public key:** `04ad6f8b8c71859ab32eb863c88f33a9c6d621639cb1b6094ee61c7a8bdfa2fd7070c620d8f0f99e98b090ce932a7ea8d7595eadd0d80ce966c52bece59b96c88f`
- **Script hex:** `4104ad6f8b8c71859ab32eb863c88f33a9c6d621639cb1b6094ee61c7a8bdfa2fd7070c620d8f0f99e98b090ce932a7ea8d7595eadd0d80ce966c52bece59b96c88fac`
- **Derived P2PKH address:** Base58Check encoding reproduces `1DRzyGtGkXYnFz9n9qxnTFbGpYBv4FNmYM`.
- **Missing segment:** The dropped substring is `XYnFz9n9qxnTFbGp`.

## Reproduction
Use the helper to verify:

```
python tools/pkscript_to_address.py <<'EOF'
1DRzyGtGk-YBv4FNmYM
Pkscript
04ad6f8b8c71859ab32eb863c88f33a9c6d621639cb1b6094ee61c7a8bdfa2fd7070c620d8f0f99e98b090ce932a7ea8d7595eadd0d80ce966c52bece59b96c88f
OP_CHECKSIG
EOF
```

The command outputs `1DRzyGtGkXYnFz9n9qxnTFbGpYBv4FNmYM`, validating the restoration.
