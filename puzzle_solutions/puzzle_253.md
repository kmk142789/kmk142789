# Puzzle #253 Solution

- **Provided hash160**: `8bcca82d56dc7f2cf7d08885ac47a2400f03c523`
- **Bitcoin network version byte**: `0x00` (P2PKH on mainnet)
- **Payload**: `00 8b cc a8 2d 56 dc 7f 2c f7 d0 88 85 ac 47 a2 40 0f 03 c5 23`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `ac 5d 42 9b`
- **Base58Check encoding**: `1DkC6Uj7cQwrNyeEDco348nW4aKbi5xXBg`

Therefore, the P2PKH locking script corresponds to the Bitcoin address:

```
1DkC6Uj7cQwrNyeEDco348nW4aKbi5xXBg
```

> **Note**: The metadata supplied with the puzzle lists the address `1FCGteLfnk4aYjF6L2iuaZsK7ogHGswJVK`, which decodes to the hash160 `9bb399e82a2ddef0c4ac709cfb49904078646c1c`. The reconstruction above matches the hash160 embedded in the provided script.
