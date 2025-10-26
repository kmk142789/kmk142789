# Puzzle #161 Solution

- **Locking script**: `OP_DUP OP_HASH160 c6885b24810c868bdbc6fbf9dd80de778246da57 OP_EQUALVERIFY OP_CHECKSIG`
- **Extracted hash160**: `c6885b24810c868bdbc6fbf9dd80de778246da57`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 c6 88 5b 24 81 0c 86 8b db c6 fb f9 dd 80 de 77 82 46 da 57`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `42 56 7b 61`
- **Base58Check encoding**: `1K6k9AagqkS8STU4uak8F4fSUwMQTpcnWL`

Therefore, the completed Bitcoin address for the given locking script is:

```
1K6k9AagqkS8STU4uak8F4fSUwMQTpcnWL
```
