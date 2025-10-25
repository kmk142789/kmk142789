# Puzzle #21 Solution

- **Given partial address:** `14oFNXucf-7riuyXs4h`
- **Provided P2PKH script:** `OP_DUP OP_HASH160 29a78213caa9eea824acf08022ab9dfc83414f56 OP_EQUALVERIFY OP_CHECKSIG`

The 20-byte hash160 in the P2PKH script corresponds to the base58check-encoded Bitcoin address:

```
14oFNXucftsHiUMY8uctg6N487riuyXs4h
```

This fills in the missing middle segment `tsHiUMY8uctg6N48`, confirming the complete destination for Puzzle #21.
