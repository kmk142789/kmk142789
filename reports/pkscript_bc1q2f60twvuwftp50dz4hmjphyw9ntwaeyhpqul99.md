# PKScript Analysis: bc1q2f60twvuwftp50dz4hmjphyw9ntwaeyhpqul99

## Summary
This record describes a SegWit P2WPKH output. Restoring the suppressed infix converts the stub `bc1q2f60t-eyhpqul99` into `bc1q2f60twvuwftp50dz4hmjphyw9ntwaeyhpqul99`.

```
bc1q2f60t-eyhpqul99
Pkscript
OP_0
5274f5b99c72561a3da2adf720dc8e2cd6eee497
```

## Details
- **Witness program:** `00145274f5b99c72561a3da2adf720dc8e2cd6eee497` follows the standard version-0, 20-byte P2WPKH layout.
- **Derived address:** Encoding the witness program with bech32 yields `bc1q2f60twvuwftp50dz4hmjphyw9ntwaeyhpqul99`.
- **Missing segment:** The hyphen compresses the substring `wvuwftp50dz4hmjphyw9ntwa` from the published address.

## Reproduction
You can recreate the address straight from the excerpt:

```
python tools/pkscript_to_address.py <<'EOF'
bc1q2f60t-eyhpqul99
Pkscript
OP_0
5274f5b99c72561a3da2adf720dc8e2cd6eee497
EOF
```

The helper emits `bc1q2f60twvuwftp50dz4hmjphyw9ntwaeyhpqul99`, confirming the decoding.
