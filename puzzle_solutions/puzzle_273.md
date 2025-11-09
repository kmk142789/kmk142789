# Puzzle #273 Solution

- **Provided hash160**: `9e786c576ee45adcbcc433d8c6ecee5908f2232b`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 9e 78 6c 57 6e e4 5a dc bc c4 33 d8 c6 ec ee 59 08 f2 23 2b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `81 3b b8 87`
- **Base58Check encoding**: `1FSv2ThziW4RBLzzgWoPraU838d2QLRR3c`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1FSv2ThziW4RBLzzgWoPraU838d2QLRR3c
```

> **Note**: The puzzle metadata lists the address `14MexPQ5VqSKDJ9KrWiWe14MKsfDCiKZ5Q`. Decoding that Base58 string corresponds
to a different hash160, so it does not match the supplied locking script.
