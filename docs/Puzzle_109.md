# Bitcoin Puzzle #109 — Completing the Legacy Address

Puzzle #109 supplies the familiar pay-to-public-key-hash (P2PKH) locking
script and a Base58Check address whose center has been suppressed:

```
1GvgAXVCb-eJcKsoyhL
Pkscript
OP_DUP
OP_HASH160
aeb0a0197442d4ade8ef41442d557b0e22b85ac0
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence confirms the standard P2PKH pattern. With the HASH160
fingerprint in hand, restoring the redacted characters is a direct
Base58Check reconstruction:

1. Prepend the mainnet version byte `0x00` to the 20-byte hash.
2. Double-SHA256 hash the 21-byte buffer and keep the first four bytes as the
   checksum.
3. Append the checksum and encode the 25-byte payload using Bitcoin's Base58
   alphabet.

Carrying out these steps recovers the full address and the missing infix:

- **Address:** `1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL`
- **Missing segment:** `A8FBjXfWiAms4ytF`

The solution matches the authoritative catalogue stored in
[`satoshi/puzzle-solutions/puzzle109.md`](../satoshi/puzzle-solutions/puzzle109.md),
which records the same HASH160 `aeb0a0197442d4ade8ef41442d557b0e22b85ac0` for
Puzzle #109.

You can reproduce the derivation with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #109\n1GvgAXVCb-eJcKsoyhL\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "aeb0a0197442d4ade8ef41442d557b0e22b85ac0\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Executing the snippet prints `1GvgAXVCbA8FBjXfWiAms4ytFeJcKsoyhL`, confirming the
restored P2PKH destination for Bitcoin Puzzle #109.
