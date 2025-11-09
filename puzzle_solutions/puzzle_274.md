# Puzzle #274 Solution

- **Provided hash160**: `486f940412cfaa7a966b4cee1f3a2ca9b9261e64`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 48 6f 94 04 12 cf aa 7a 96 6b 4c ee 1f 3a 2c a9 b9 26 1e 64`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `bb f8 51 45`
- **Base58Check encoding**: `17c1KQD6FqWhE33bbqPbTh1Ad3A8eoz6sN`

Therefore, the completed Bitcoin address for the provided locking script is:

```
17c1KQD6FqWhE33bbqPbTh1Ad3A8eoz6sN
```

> **Note**: The puzzle metadata lists the address `19vXeuKFzqG6dSnx2Du18CSPjSTBkkwgXk`, but decoding that Base58 string yields a different (and invalid) checksum, so it does not match the supplied locking script.
