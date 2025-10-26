# Puzzle #198 Solution

- **Locking script**: `OP_DUP OP_HASH160 ba644a0cd09495d4232349634116e0f98c8c3b96 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `ba644a0cd09495d4232349634116e0f98c8c3b96`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ba 64 4a 0c d0 94 95 d4 23 23 49 63 41 16 e0 f9 8c 8c 3b 96`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `60 f4 24 f5`
- **Base58Check encoding**: `1HzYpuDW1vNwWthvbNT8R5Y5j5jW3Kd3eC`

Therefore, the completed Bitcoin address for the given locking script is:

```
1HzYpuDW1vNwWthvbNT8R5Y5j5jW3Kd3eC
```
