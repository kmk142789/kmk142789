# Puzzle #264 Solution

- **Provided hash160**: `dba61e845814b1a04cab48785056ebfd985757c6`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 db a6 1e 84 58 14 b1 a0 4c ab 48 78 50 56 eb fd 98 57 57 c6`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `2c 9c e0 0e`
- **Base58Check encoding**: `1M2PzBC5JZ2Po3y3ARb5C8cMPF89ff5XjK`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1M2PzBC5JZ2Po3y3ARb5C8cMPF89ff5XjK
```

> **Note**: The metadata lists the address `157C3e2UhMZ9HrXYqrxY8kpkhshHU6PqXZ`, but decoding that Base58 string yields the
> hash160 `2d0c381e87ac6f1f28ad52d17eccd5ad24981c4e` with a checksum mismatch (`effdc44c` vs. `d206a852`), so it does not
> correspond to the supplied locking script.
