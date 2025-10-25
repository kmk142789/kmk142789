# Puzzle #284 Solution

- **Provided Base58 clue**: `14RdpvaEtsmjirP7pa2mJi3UJhbfz5A9yN`
- **PK script**: `OP_DUP OP_HASH160 587284b200e66073dbe5a99a89a3a63a1511441c OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `587284b200e66073dbe5a99a89a3a63a1511441c`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 58 72 84 b2 00 e6 60 73 db e5 a9 9a 89 a3 a6 3a 15 11 44 1c`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `11 cb 39 e8`
- **Base58Check encoding**: `194feknXENGw3Yefyc5abXqa1UYuRqJaco`

Therefore, the completed Bitcoin address for the given locking script is:

```
194feknXENGw3Yefyc5abXqa1UYuRqJaco
```
