# Puzzle #128 Solution

- **Provided Base58 clue**: `1MZ2L1gFr-THw9gNwaj`
- **PK script**: `OP_DUP OP_HASH160 e170ef514689d7230da362a0c121a07723550512 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `e170ef514689d7230da362a0c121a07723550512`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 e1 70 ef 51 46 89 d7 23 0d a3 62 a0 c1 21 a0 77 23 55 05 12`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))`
- **Base58Check encoding**: `1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj`

Therefore, the completed Bitcoin address for the given locking script (filling the gap in the clue) is:

```
1MZ2L1gFrCtkkn6DnTT2e4PFUTHw9gNwaj
```
