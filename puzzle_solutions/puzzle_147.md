# Puzzle #147 Solution

- **Locking script**: `OP_DUP OP_HASH160 5318b9d7fcc93873f768725eb68ba2c924bb07ee OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `5318b9d7fcc93873f768725eb68ba2c924bb07ee`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 53 18 b9 d7 fc c9 38 73 f7 68 72 5e b6 8b a2 c9 24 bb 07 ee`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `23 a2 21 a9`
- **Base58Check encoding**: `18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL`

Therefore, the completed Bitcoin address for the given locking script is:

```
18aNhurEAJsw6BAgtANpexk5ob1aGTwSeL
```
