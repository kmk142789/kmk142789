# Puzzle #177 Solution

- **Locking script**: `OP_DUP OP_HASH160 e8d34bcbeff242d7941a9465d22c41d1c51e80d0 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e8d34bcbeff242d7941a9465d22c41d1c51e80d0`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e8 d3 4b cb ef f2 42 d7 94 1a 94 65 d2 2c 41 d1 c5 1e 80 d0`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `47 e8 4c c2`
- **Base58Check encoding**: `1NE4tcbXtbLkuGWF1QopvLJHGYN9bXrQnD`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NE4tcbXtbLkuGWF1QopvLJHGYN9bXrQnD
```
