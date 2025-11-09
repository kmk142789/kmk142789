# Puzzle #280 Solution

- **Provided hash160**: `1cffa97b4c387f395ef7f62fd13c79c1bd39e183`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 1c ff a9 7b 4c 38 7f 39 5e f7 f6 2f d1 3c 79 c1 bd 39 e1 83`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `3a 46 9c 74`
- **Base58Check encoding**: `13eLC5hdnDPDLDGd7jux4sVunkYPqpPUnP`

Therefore, the completed Bitcoin address for the provided locking script is:

```
13eLC5hdnDPDLDGd7jux4sVunkYPqpPUnP
```

> **Note**: The puzzle metadata lists the address `16qBeBkmqrgddRwoSAorSvxnMpkcvji7Df`. Decoding that Base58 string corresponds
> to a different hash160, so it does not match the supplied locking script.
