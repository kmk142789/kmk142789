# Puzzle #251 — Filling in the Missing Base58 Middle

The puzzle supplied the first and last characters of a Bitcoin address and the
full P2PKH locking script:

```
OP_DUP OP_HASH160 dbeecf6406c1569a483a88e35ed349a521a414ca OP_EQUALVERIFY OP_CHECKSIG
```

Because the script is the standard legacy (P2PKH) template, the solution is to
prepend the mainnet version byte (`0x00`), compute the double-SHA256 checksum,
and Base58Check encode the result.

Run the existing helper script:

```bash
python scripts/solve_puzzle256.py dbeecf6406c1569a483a88e35ed349a521a414ca
```

Output:

```
1M3u4q5Q35qtQPmDHeubVbk7APYi3VVoBX
```

This fills in the missing middle of the puzzle string `1M3u4q5Q3-PYi3VVoBX` and
confirms that the recovered address is the unique one that spends from the
provided locking script.
