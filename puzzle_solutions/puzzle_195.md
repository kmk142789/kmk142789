# Puzzle #195 Solution

- **Locking script**: `OP_DUP OP_HASH160 45afd78f30bfcfa9833d9fbef24a52971729fed4 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `45afd78f30bfcfa9833d9fbef24a52971729fed4`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 45 af d7 8f 30 bf cf a9 83 3d 9f be f2 4a 52 97 17 29 fe d4`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `66 64 e6 02`
- **Base58Check encoding**: `17MUGxNQznCu8dTbyiCXx1bdmhWBYPmHcu`

Therefore, the completed Bitcoin address for the given locking script is:

```
17MUGxNQznCu8dTbyiCXx1bdmhWBYPmHcu
```
