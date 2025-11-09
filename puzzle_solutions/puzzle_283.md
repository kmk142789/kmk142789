# Puzzle #283 Solution

- **Provided hash160**: `a4e600e5f134e5af85acd4635251767d4752efd3`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 a4 e6 00 e5 f1 34 e5 af 85 ac d4 63 52 51 76 7d 47 52 ef d3`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `5e 29 e8 92`
- **Base58Check encoding**: `1G2uMPHE4W6fDxxLA5qzDKf9nGNjNnkc6s`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1G2uMPHE4W6fDxxLA5qzDKf9nGNjNnkc6s
```

> **Note**: The puzzle metadata lists the address `1GTiiarCSkdeLrcvc2j783XnhiNEuy57dJ`, but decoding that Base58 string yields a different hash160 and checksum, so it does not match the supplied locking script.
