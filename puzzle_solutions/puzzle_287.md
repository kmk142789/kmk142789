---
status: documented
---
# Puzzle #287 Solution

- **Provided Base58 clue**: `1BxULzBofzJfBYYD8RgBNdQT2MzDj7Su4R`
- **PK script**: `OP_DUP OP_HASH160 2ac697ed1903af7f4b3b77b21471b749891213e8 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2ac697ed1903af7f4b3b77b21471b749891213e8`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2a c6 97 ed 19 03 af 7f 4b 3b 77 b2 14 71 b7 49 89 12 13 e8`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `2c 32 87 c9`
- **Base58Check encoding**: `14uBHaCs4aaM3fPjdNTyW1hApXGeT7TEaC`

Therefore, the completed Bitcoin address for the given locking script is:

```
14uBHaCs4aaM3fPjdNTyW1hApXGeT7TEaC
```

> **Note**: The puzzle metadata lists the address `1BxULzBofzJfBYYD8RgBNdQT2MzDj7Su4R`, but decoding that Base58 string yields the hash160 `782ef63b97b845746a9a714b5e0d8d7df56aee9d`, which does not match the supplied locking script.
