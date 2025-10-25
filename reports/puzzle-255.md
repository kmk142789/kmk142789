# Puzzle #255 Solution

The provided script is a standard P2PKH (pay-to-public-key-hash) Bitcoin locking script:

```
OP_DUP OP_HASH160 460528d920ce045d9f6fc319182960707b248064 OP_EQUALVERIFY OP_CHECKSIG
```

To obtain the corresponding Base58Check-encoded Bitcoin address:

1. Prepend the mainnet version byte `0x00` to the 20-byte public key hash.
2. Compute the double-SHA256 checksum and append the first four checksum bytes.
3. Encode the result using the Base58 alphabet.

Carrying out these steps yields the address:

```
17PEUvQmgqPkkvRkMowoR1wRDXYzre4b9Z
```

This matches the expected P2PKH address for the supplied hash.
