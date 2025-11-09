# Puzzle #267 Solution

- **Provided hash160**: `97dfc24e80c9c77b0dd0954807e137d8fdad3c04`
- **Bitcoin network version byte**: `0x00` (for a P2PKH mainnet address)
- **Payload**: `00 97 df c2 4e 80 c9 c7 7b 0d d0 95 48 07 e1 37 d8 fd ad 3c 04`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `19 d2 d2 0f`
- **Base58Check encoding**: `1Er361sRzv3p139dkVSGerghEukSe9xAX8`

Therefore, the completed Bitcoin address for the provided locking script is:

```
1Er361sRzv3p139dkVSGerghEukSe9xAX8
```

> **Note**: The puzzle metadata lists the address `1C4fz2quQH2PieCxbKjgSBCdTBNNxD7S1v`, but decoding that Base58 string yields the hash160 `795b2c526820af4ca62befeea099f2f572aaead7`, so it does not correspond to the supplied locking script.
