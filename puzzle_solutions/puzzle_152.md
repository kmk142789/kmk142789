# Puzzle #152 Solution

- **Locking script**: `OP_DUP OP_HASH160 da56cd815fa2f0d6a4ce6d25ed7b1a01d9f9bc6b OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `da56cd815fa2f0d6a4ce6d25ed7b1a01d9f9bc6b`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 da 56 cd 81 5f a2 f0 d6 a4 ce 6d 25 ed 7b 1a 01 d9 f9 bc 6b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `ce 5d 66 9c`
- **Base58Check encoding**: `1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN`

Therefore, the completed Bitcoin address for the given locking script is:

```
1LuUHyrQr8PKSvbcY1v1PiuGuqFjWpDumN
```
