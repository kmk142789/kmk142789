# Puzzle #251 P2PKH Reconstruction

The puzzle provides the standard six-line wallet export format consisting of a
hyphenated Base58Check address hint and the canonical legacy pay-to-public-key-
hash (P2PKH) locking script:

```
1M3u4q5Q3-PYi3VVoBX
Pkscript
OP_DUP
OP_HASH160
dbeecf6406c1569a483a88e35ed349a521a414ca
OP_EQUALVERIFY
OP_CHECKSIG
```

Because the script matches the legacy template, solving the puzzle amounts to
Base58Check encoding the supplied HASH160 fingerprint.

1. Prefix the 20-byte HASH160 digest with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte payload and append the
   first four bytes of the digest.
3. Encode the resulting 25-byte buffer with the Bitcoin Base58 alphabet.

The helper already shipped in the repository reproduces the missing middle of
the address:

```bash
python scripts/solve_puzzle256.py dbeecf6406c1569a483a88e35ed349a521a414ca
# -> 1M3u4q5Q35qtQPmDHeubVbk7APYi3VVoBX
```

The reconstructed destination matches the consensus entry recorded in the
puzzle index and confirms that the published script is a classic P2PKH output.
