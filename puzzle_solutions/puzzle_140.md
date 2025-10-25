# Puzzle #140 Solution

- **Locking script**: `OP_DUP OP_HASH160 9a592939779b8230d8063a2b11a5dc2f0ce6b93c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `9a592939779b8230d8063a2b11a5dc2f0ce6b93c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 9a 59 29 39 77 9b 82 30 d8 06 3a 2b 11 a5 dc 2f 0c e6 b9 3c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `1f 4e 4b 47`
- **Base58Check encoding**: `1F57sZRikB3SmiFd8MaApA2DB4w3hsSR74`

Therefore, the completed Bitcoin address for the given locking script is:

```
1F57sZRikB3SmiFd8MaApA2DB4w3hsSR74
```
