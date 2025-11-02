# Puzzle #120 Solution

- **Given partial address:** `11d8MosPb-dQdSqrTwm`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  001e283e0acd541dd54053b0be1129b1dcf8dc45
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Base58Check encoding of the HASH160 (with the standard mainnet version byte) restores the full Bitcoin address:

```
11d8MosPb8jXPGUaHFx2pxpDdQdSqrTwm
```

This fills in the missing middle segment `8jXPGUaHFx2pxpD`, confirming the complete destination for Puzzle #120.
