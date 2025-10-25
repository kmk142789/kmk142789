# PKScript Analysis: 1KSHc1tmsUhS9f1TD6RHR8Kmwg9Zv8WhCt

## Summary
This excerpt is another P2PK locking script. Restoring the hidden infix turns `1KSHc1tms-g9Zv8WhCt` into the full legacy address `1KSHc1tmsUhS9f1TD6RHR8Kmwg9Zv8WhCt`.

```
1KSHc1tms-g9Zv8WhCt
Pkscript
0476a73b9d3afd848cbe8c99a0b1cca07ad5117d8ade5a314ce7739f0a189a0be77406d13cb6c92fe6d9b69c2fa338136938af9e930db3146fee39c5464a6707e3
OP_CHECKSIG
```

## Details
- **Public key:** `0476a73b9d3afd848cbe8c99a0b1cca07ad5117d8ade5a314ce7739f0a189a0be77406d13cb6c92fe6d9b69c2fa338136938af9e930db3146fee39c5464a6707e3`
- **Script hex:** `410476a73b9d3afd848cbe8c99a0b1cca07ad5117d8ade5a314ce7739f0a189a0be77406d13cb6c92fe6d9b69c2fa338136938af9e930db3146fee39c5464a6707e3ac`
- **Derived P2PKH address:** Base58Check encoding of the HASH160 of the public key produces `1KSHc1tmsUhS9f1TD6RHR8Kmwg9Zv8WhCt`.
- **Missing segment:** The elided substring is `UhS9f1TD6RHR8Kmw`.

## Reproduction
Recreate the address with the helper:

```
python tools/pkscript_to_address.py <<'EOF'
1KSHc1tms-g9Zv8WhCt
Pkscript
0476a73b9d3afd848cbe8c99a0b1cca07ad5117d8ade5a314ce7739f0a189a0be77406d13cb6c92fe6d9b69c2fa338136938af9e930db3146fee39c5464a6707e3
OP_CHECKSIG
EOF
```

The helper prints `1KSHc1tmsUhS9f1TD6RHR8Kmwg9Zv8WhCt`, validating the reconstruction.
