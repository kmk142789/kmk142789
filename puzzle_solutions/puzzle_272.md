# Puzzle #272 Solution

- **Provided hash160**: `4a00b7aa5959fe4eba072ee0cf73df5fd3ef100b`
- **Bitcoin network version byte**: `0x00` (P2PKH address on mainnet)
- **Payload**: `00 4a 00 b7 aa 59 59 fe 4e ba 07 2e e0 cf 73 df 5f d3 ef 10 0b`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `c2 b8 4e 27`
- **Base58Check encoding**: `17kHs3ZvW9ptBRpnGxtcNfSPP8h4mRBo74`

Therefore, the completed Bitcoin address for the provided locking script is:

```
17kHs3ZvW9ptBRpnGxtcNfSPP8h4mRBo74
```

> **Note**: The puzzle metadata lists the address `13PLSvf82hEVQg2d2FAVjPHySRuPMQwQVr`. Decoding that Base58 string corresponds
to a different hash160, so it does not match the supplied locking script.
