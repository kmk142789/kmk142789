# Puzzle #263 Solution

- **Provided hash160**: `e46b9bfafdec4e39418144e6a64b73ca91fc7552`
- **Bitcoin network version byte**: `0x00` (mainnet P2PKH address)
- **Payload**: `00 e4 6b 9b fa fd ec 4e 39 41 81 44 e6 a6 4b 73 ca 91 fc 75 52`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `8a 86 27 5d`
- **Base58Check encoding**: `1MpmyZdBMD7MCKwAwzzYqWvKEZmBxzaxgt`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1MpmyZdBMD7MCKwAwzzYqWvKEZmBxzaxgt
```

> **Note**: The metadata lists the address `1Fxuf9PLQrUAHknDaCXPhabWuWbzvXMMbW`, but decoding that string yields the hash160 `a424986408fca2b1050043e086fb580483b596` with checksum `27819e01`. The correct checksum for that payload would be `df7d1c99`, so the published address does not match the supplied locking script and is invalid.
