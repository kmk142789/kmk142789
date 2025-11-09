# Puzzle #271 Solution

- **Provided hash160**: `7ae451d745fd45fe9b95d7c2af368baacb91f8c8`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 7a e4 51 d7 45 fd 45 fe 9b 95 d7 c2 af 36 8b aa cb 91 f8 c8`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `b8 96 c8 c9`
- **Base58Check encoding**: `1CCnxLM6TwEVjpNWeZWL2MJF9dTxUfovcx`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1CCnxLM6TwEVjpNWeZWL2MJF9dTxUfovcx
```

> **Note**: The puzzle metadata lists the address `17PXoEAN95s28NHG1pGB5ozpZWf8HevRmz`. Decoding that Base58 string corresponds
to a different hash160, so it does not match the supplied locking script.
