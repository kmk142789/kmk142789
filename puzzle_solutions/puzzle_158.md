# Puzzle #158 Solution

- **Locking script**: `OP_DUP OP_HASH160 2d7b48e2c224676caac4d30b0b185c593f9bdc12 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2d7b48e2c224676caac4d30b0b185c593f9bdc12`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2d 7b 48 e2 c2 24 67 6c aa c4 d3 0b 0b 18 5c 59 3f 9b dc 12`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `5a 8b 85 b6`
- **Base58Check encoding**: `159V6c3WkdishY2cu1J2P4Add1NoG5P18H`

Therefore, the completed Bitcoin address for the given locking script is:

```
159V6c3WkdishY2cu1J2P4Add1NoG5P18H
```
