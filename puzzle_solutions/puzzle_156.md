# Puzzle #156 Solution

- **Locking script**: `OP_DUP OP_HASH160 9ea3f29aaedf7da10b1488934c50a39e271b0b64 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `9ea3f29aaedf7da10b1488934c50a39e271b0b64`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 9e a3 f2 9a ae df 7d a1 0b 14 88 93 4c 50 a3 9e 27 1b 0b 64`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e1 02 86 1b`
- **Base58Check encoding**: `1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE`

Therefore, the completed Bitcoin address for the given locking script is:

```
1FTpAbQa4h8trvhQXjXnmNhqdiGBd1oraE
```
