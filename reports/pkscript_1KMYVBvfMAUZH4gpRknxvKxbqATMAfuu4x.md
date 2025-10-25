# PKScript Analysis: 1KMYVBvfMAUZH4gpRknxvKxbqATMAfuu4x

## Summary
This is another pay-to-public-key transcript. Restoring the masked section changes `1KMYVBvfM-ATMAfuu4x` into the full address `1KMYVBvfMAUZH4gpRknxvKxbqATMAfuu4x`.

```
1KMYVBvfM-ATMAfuu4x
Pkscript
04580bf58d578798b7ac68e19e933ffe544045b43b05ec4b2a40b5da5371664bd88bd008ce766a37607ea34b29b18e2a6a0bd1c47d025eeddf6afd88a193cacdac
OP_CHECKSIG
```

## Details
- **Public key:** `04580bf58d578798b7ac68e19e933ffe544045b43b05ec4b2a40b5da5371664bd88bd008ce766a37607ea34b29b18e2a6a0bd1c47d025eeddf6afd88a193cacdac`
- **Script hex:** `4104580bf58d578798b7ac68e19e933ffe544045b43b05ec4b2a40b5da5371664bd88bd008ce766a37607ea34b29b18e2a6a0bd1c47d025eeddf6afd88a193cacdacac`
- **Derived P2PKH address:** Hashing the key and encoding with Base58Check yields `1KMYVBvfMAUZH4gpRknxvKxbqATMAfuu4x`.
- **Missing segment:** The omitted substring is `AUZH4gpRknxvKxbq`.

## Reproduction
Confirm with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
1KMYVBvfM-ATMAfuu4x
Pkscript
04580bf58d578798b7ac68e19e933ffe544045b43b05ec4b2a40b5da5371664bd88bd008ce766a37607ea34b29b18e2a6a0bd1c47d025eeddf6afd88a193cacdac
OP_CHECKSIG
EOF
```

This prints `1KMYVBvfMAUZH4gpRknxvKxbqATMAfuu4x`, verifying the reconstruction.
