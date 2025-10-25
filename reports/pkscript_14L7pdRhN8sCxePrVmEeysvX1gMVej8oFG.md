# PKScript Analysis: 14L7pdRhN8sCxePrVmEeysvX1gMVej8oFG

## Summary
The supplied transcript expands to the textbook pay-to-public-key-hash (P2PKH) locking script. It duplicates the top stack item,
computes the RIPEMD160(SHA256(pubkey)) digest, compares it to the embedded hash160 value `2485f982e89499382f8bfe3824e818dceb1724d7`,
and finally enforces signature verification with `OP_CHECKSIG`.

## Details
- **Hash160:** `2485f982e89499382f8bfe3824e818dceb1724d7`
- **Script hex:** `76a9142485f982e89499382f8bfe3824e818dceb1724d788ac`
- **Address restoration:** The heading `14L7pdRhN-gMVej8oFG` keeps the first five and last ten Base58 characters of the address while replacing the
  omitted middle segment with a hyphen. Reinserting the missing characters (`8sCxePrVmEeysvX1`) reproduces the full legacy address
  `14L7pdRhN8sCxePrVmEeysvX1gMVej8oFG`.

## Reproduction
The helper utility in this repository confirms the reconstruction:

```
python tools/pkscript_to_address.py <<'EOF'
14L7pdRhN-gMVej8oFG
Pkscript
OP_DUP
OP_HASH160
2485f982e89499382f8bfe3824e818dceb1724d7
OP_EQUALVERIFY
OP_CHECKSIG
EOF
```

Running the command recovers the canonical Base58Check address `14L7pdRhN8sCxePrVmEeysvX1gMVej8oFG`.
