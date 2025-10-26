# Puzzle #196 Solution

- **Locking script**: `OP_DUP OP_HASH160 3a6909e7c4883bcb34595bfad8335037f926ae02 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `3a6909e7c4883bcb34595bfad8335037f926ae02`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 3a 69 09 e7 c4 88 3b cb 34 59 5b fa d8 33 50 37 f9 26 ae 02`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `4a 6d bd f2`
- **Base58Check encoding**: `16Kr2Ls7TT1qfRJNZB8mh8X4FBKqutxfBF`

Therefore, the completed Bitcoin address for the given locking script is:

```
16Kr2Ls7TT1qfRJNZB8mh8X4FBKqutxfBF
```
