# Puzzle #138 Solution

- **Locking script**: `OP_DUP OP_HASH160 da6863c888964b0cd01fe5f694146d7415352753 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `da6863c888964b0cd01fe5f694146d7415352753`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 da 68 63 c8 88 96 4b 0c d0 1f e5 f6 94 14 6d 74 15 35 27 53`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `2a ea a1 91`
- **Base58Check encoding**: `1LuqMwz6ihf5vCsN8L1w4ctSEoH1ioM2Sc`

Therefore, the completed Bitcoin address for the given locking script is:

```
1LuqMwz6ihf5vCsN8L1w4ctSEoH1ioM2Sc
```
