# Puzzle #293 Solution

- **Provided hash160**: `12153fe11837ae30ffb24caa87ec5470fe296afa`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 12 15 3f e1 18 37 ae 30 ff b2 4c aa 87 ec 54 70 fe 29 6a fa`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `c0 c8 e8 c0`
- **Base58Check encoding**: `12ecctyNEfkwgawVhsTrt4eHcymcSip5uZ`

Therefore, the completed Bitcoin address for the provided locking script is:

```
12ecctyNEfkwgawVhsTrt4eHcymcSip5uZ
```

> **Note**: The puzzle metadata lists the address `19gznNB12HvbtMCRTc1gkmjBKMBQQ1C6bL`. Decoding that Base58 string corresponds
to a different hash160, so it does not match the supplied locking script.
