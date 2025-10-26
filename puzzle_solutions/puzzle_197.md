# Puzzle #197 Solution

- **Locking script**: `OP_DUP OP_HASH160 78457bc2c3fbfadf389ad888b161a2aa3f0534d1 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `78457bc2c3fbfadf389ad888b161a2aa3f0534d1`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 78 45 7b c2 c3 fb fa df 38 9a d8 88 b1 61 a2 aa 3f 05 34 d1`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `d8 64 92 2b`
- **Base58Check encoding**: `13oQsTUDmRgHjrPHCe6kWok5ZDsy6C5HS5`

Therefore, the completed Bitcoin address for the given locking script is:

```
13oQsTUDmRgHjrPHCe6kWok5ZDsy6C5HS5
```
