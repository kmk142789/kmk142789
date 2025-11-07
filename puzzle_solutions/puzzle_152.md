# Puzzle #152 Solution

- **Locking script**: `OP_DUP OP_HASH160 726d0d46b426c973ebbfa3bf0e4ac97fa952676f OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `726d0d46b426c973ebbfa3bf0e4ac97fa952676f`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 72 6d 0d 46 b4 26 c9 73 eb bf a3 bf 0e 4a c9 7f a9 52 67 6f`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `de db a3 ef`
- **Base58Check encoding**: `1BUz7m6FrSRtkRGL4fYmtsfSExpr19QU3X`

Therefore, the completed Bitcoin address for the given locking script is:

```
1BUz7m6FrSRtkRGL4fYmtsfSExpr19QU3X
```
