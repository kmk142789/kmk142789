# Puzzle #128 Solution

- **Provided Base58 clue**: `1EdAw4EMk-5chSg5ev6`
- **PK script**: `OP_DUP OP_HASH160 9570e68f5fad1b67f9ed9fea078fe9ef4767815b OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `9570e68f5fad1b67f9ed9fea078fe9ef4767815b`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 95 70 e6 8f 5f ad 1b 67 f9 ed 9f ea 07 8f e9 ef 47 67 81 5b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))`
- **Base58Check encoding**: `1EdAw4EMkXUU8R3QdeesjWNSW5chSg5ev6`

Therefore, the completed Bitcoin address for the given locking script (filling the gap in the clue) is:

```
1EdAw4EMkXUU8R3QdeesjWNSW5chSg5ev6
```
