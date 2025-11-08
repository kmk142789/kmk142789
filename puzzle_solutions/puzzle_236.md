# Puzzle #236 Solution

- **Provided hash160**: `c7641aef27606662eaef7b00ea64ba7b3f3b68ee`
- **Bitcoin network version byte**: `0x00` (P2PKH on mainnet)
- **Payload**: `00 c7 64 1a ef 27 60 66 62 ea ef 7b 00 ea 64 ba 7b 3f 3b 68 ee`
- **Checksum**: First four bytes of `SHA256(SHA256(payload))` = `7b d0 3b cf`
- **Base58Check encoding**: `1KBHPcAbFABffHaeD1L6FEkPiyEngCi6q4`

Therefore, the Bitcoin address corresponding to the provided locking script is:

```
1KBHPcAbFABffHaeD1L6FEkPiyEngCi6q4
```

*Note:* The derived address above is consistent with the supplied hash160, even though it differs from the address that accompanied the puzzle metadata.
