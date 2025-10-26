# Bitcoin Output Analysis: c7314cd30cbd9a598585515e487bcb16548f6efea09cab0f679198e341d3dab3:2

## Output Summary
- **Type:** Native SegWit Pay-to-Witness-Public-Key-Hash (P2WPKH, version 0)
- **scriptPubKey (ASM):** `OP_0 OP_PUSHBYTES_20 70f1628aa7e79b245f70096934816e6480af4699`
- **scriptPubKey (Hex):** `001470f1628aa7e79b245f70096934816e6480af4699`

## Decoded Address
Using the SegWit version 0 witness program (`70f1628aa7e79b245f70096934816e6480af4699`) and human-readable part `bc`, the corresponding Bech32 address is:

```
bc1qwrck9z48u7djghmsp95nfqtwvjq2735emfnt5m
```

## Spending Transaction
- **Spent by:** Output index 2 of transaction `c7314cd30cbd9a598585515e487bcb16548f6efea09cab0f679198e341d3dab3`
- **Block Height:** 917,883

## Notes
- The witness program length (20 bytes) confirms the P2WPKH format.
- Native SegWit outputs do not include the public key hash directly in legacy Base58Check format; instead, they require Bech32 encoding with the witness version prefix (`0`) and the converted 5-bit groups of the 20-byte hash.
- The decoded address `bc1qwrck9z48u7djghmsp95nfqtwvjq2735emfnt5m` can be used to verify the output on block explorers that support SegWit addresses.
