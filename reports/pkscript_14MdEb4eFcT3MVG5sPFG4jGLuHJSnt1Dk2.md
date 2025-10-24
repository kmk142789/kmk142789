# PKScript Analysis: 14MdEb4eFcT3MVG5sPFG4jGLuHJSnt1Dk2

## Summary
The supplied transcript corresponds to the canonical pay-to-public-key-hash (P2PKH) locking script. After duplicating the stack top element with `OP_DUP`, it hashes the value using `OP_HASH160`, compares the result to the embedded 20-byte digest via `OP_EQUALVERIFY`, and finally enforces signature verification with `OP_CHECKSIG` (presented across the `OP_CH` / `ECKSIG` lines in the source text).

```
OP_DUP OP_HASH160 24cef184714bbd030833904f5265c9c3e12a95a2 OP_EQUALVERIFY OP_CHECKSIG
```

## Details
- **Hash payload:** The 20-byte payload `24cef184714bbd030833904f5265c9c3e12a95a2` matches the HASH160 digest embedded in the script.
- **Derived address:** Prefixing the digest with the Bitcoin mainnet version byte (`0x00`) and performing Base58Check encoding yields the address `14MdEb4eFcT3MVG5sPFG4jGLuHJSnt1Dk2`.
- **Formatting artefact:** The heading line `14MdEb4eF-HJSnt1Dk2` omits the central characters and introduces a hyphen. Restoring the removed segment (`cT3MVG5sPFG4jGLu`) reconstructs the canonical address shown above.

## Reproduction
The repository helper can be used to confirm the interpretation:

```
python tools/pkscript_to_address.py <<'EOF'
14MdEb4eF-HJSnt1Dk2
Pkscript
OP_DUP
OP_HASH160
24cef184714bbd030833904f5265c9c3e12a95a2
OP_EQUALVERIFY
OP_CH
ECKSIG
EOF
```

Executing the helper outputs `14MdEb4eFcT3MVG5sPFG4jGLuHJSnt1Dk2`, matching the derived address.
