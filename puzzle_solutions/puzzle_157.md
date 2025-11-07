# Puzzle #157 Solution

- **Locking script**: `OP_DUP OP_HASH160 641f536a48428bba935a7efe7016821cddd1fc57 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `641f536a48428bba935a7efe7016821cddd1fc57`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 64 1f 53 6a 48 42 8b ba 93 5a 7e fe 70 16 82 1c dd d1 fc 57`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `09 db d6 8e`
- **Base58Check encoding**: `1A8Q6jxNJyLexhXx4pLFCCswBoFHmQqGP7`

Therefore, the completed Bitcoin address for the given locking script is:

```
1A8Q6jxNJyLexhXx4pLFCCswBoFHmQqGP7
```
