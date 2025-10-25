# Puzzle #127 Solution

- **Provided Base58 clue**: `1G6EFyBRU-sA7w7nzi4`
- **PK script**: `OP_DUP OP_HASH160 a58708aa98ad35c889bb36d8049bf9e9cacfd02a OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `a58708aa98ad35c889bb36d8049bf9e9cacfd02a`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 a5 87 08 aa 98 ad 35 c8 89 bb 36 d8 04 9b f9 e9 ca cf d0 2a`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))`
- **Base58Check encoding**: `1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4`

Therefore, the completed Bitcoin address for the given locking script (filling the gap in the clue) is:

```
1G6EFyBRU86sThN3SSt3GrHu1sA7w7nzi4
```
