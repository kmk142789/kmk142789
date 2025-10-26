# Puzzle #207 Solution

- **Provided hash160**: `0d1da571308466802a10e1792b0018a4479b1dbc`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 0d 1d a5 71 30 84 66 80 2a 10 e1 79 2b 00 18 a4 47 9b 1d bc`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` → `1c 65 af cd`
- **Base58Check encoding**: `12CMJMQvgAraLZZKA16C8jbwirthyi5y24`

Therefore, the completed Bitcoin address for the given locking script is:

```
12CMJMQvgAraLZZKA16C8jbwirthyi5y24
```
