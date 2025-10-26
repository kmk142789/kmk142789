# Puzzle #159 Solution

- **Locking script**: `OP_DUP OP_HASH160 2ac1295b4e54b3f15bb0a99f84018d2082495645 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `2ac1295b4e54b3f15bb0a99f84018d2082495645`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 2a c1 29 5b 4e 54 b3 f1 5b b0 a9 9f 84 01 8d 20 82 49 56 45`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `e0 c5 06 46`
- **Base58Check encoding**: `14u4nA5sugaswb6SZgn5av2vuChdMnD9E5`

Therefore, the completed Bitcoin address for the given locking script is:

```
14u4nA5sugaswb6SZgn5av2vuChdMnD9E5
```
