# Puzzle #178 Solution

- **Locking script**: `OP_DUP OP_HASH160 2bbe5ef5cecd3905a847f2b33ac65ac91fd35dbc OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2bbe5ef5cecd3905a847f2b33ac65ac91fd35dbc`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2b be 5e f5 ce cd 39 05 a8 47 f2 b3 3a c6 5a c9 1f d3 5d bc`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `0f a7 6d d8`
- **Base58Check encoding**: `14zJ7TJBoKnBxEjPqdC2hYvmXLR8XMMZ7V`

Therefore, the completed Bitcoin address for the given locking script is:

```
14zJ7TJBoKnBxEjPqdC2hYvmXLR8XMMZ7V
```
