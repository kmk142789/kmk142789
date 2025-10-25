# Puzzle #135 Solution

- **Locking script**: `OP_DUP OP_HASH160 036544dfa1527127c007d1b35f44c558e09e6a38 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `036544dfa1527127c007d1b35f44c558e09e6a38`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 03 65 44 df a1 52 71 27 c0 07 d1 b3 5f 44 c5 58 e0 9e 6a 38`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `91 1c 57 e4`
- **Base58Check encoding**: `1JxLsYvf6qw5Znh1DwrdS9Uf18SFMQMSK`

Therefore, the completed Bitcoin address for the given locking script is:

```
1JxLsYvf6qw5Znh1DwrdS9Uf18SFMQMSK
```
