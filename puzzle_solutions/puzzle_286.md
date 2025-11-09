---
status: documented
---
# Puzzle #286 Solution

- **Provided Base58 clue**: `1HsoJ9ZGqMkeMfukNSA1GMPT5YehcTGBxK`
- **PK script**: `OP_DUP OP_HASH160 aa636a131f48732a03f575357e797b4a065835ef OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `aa636a131f48732a03f575357e797b4a065835ef`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 aa 63 6a 13 1f 48 73 2a 03 f5 75 35 7e 79 7b 4a 06 58 35 ef`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `39 c2 e7 cd`
- **Base58Check encoding**: `1GXvy3Qx6HdmmGJXHRjrxs3UzZuFA4b8ha`

Therefore, the completed Bitcoin address for the given locking script is:

```
1GXvy3Qx6HdmmGJXHRjrxs3UzZuFA4b8ha
```
