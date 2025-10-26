# Puzzle #173 Solution

- **Locking script**: `OP_DUP OP_HASH160 ee8c71eba975eaea433675f44e4899da568a840c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `ee8c71eba975eaea433675f44e4899da568a840c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 ee 8c 71 eb a9 75 ea ea 43 36 75 f4 4e 48 99 da 56 8a 84 0c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `74 0c 22 97`
- **Base58Check encoding**: `1NkL4wqYWKMRwJkpEEubg2uUeQcip1momg`

Therefore, the completed Bitcoin address for the given locking script is:

```
1NkL4wqYWKMRwJkpEEubg2uUeQcip1momg
```
