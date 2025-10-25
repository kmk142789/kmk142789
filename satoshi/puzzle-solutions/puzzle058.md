# Puzzle #58 Solution

- **Given partial address:** `1Dn8NF8qD-mZXgvosXf`
- **Provided P2PKH script:**
  ```
  OP_DUP
  OP_HASH160
  8c2a6071f89c90c4dab5ab295d7729d1b54ea60f
  OP_EQUALVERIFY
  OP_CHECKSIG
  ```

Encoding the supplied HASH160 with the Bitcoin mainnet P2PKH version byte (0x00) reproduces the complete destination address:

```
1Dn8NF8qDyyfHMktmuoQLGyjWmZXgvosXf
```

The reconstruction fills in the missing core segment `yyfHMktmuoQLGyjW`, yielding the full address that spends Puzzle #58.
