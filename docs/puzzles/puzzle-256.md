# Puzzle #256 — Reconstructing the Address

The puzzle supplied a partial Bitcoin address along with the full P2PKH locking
script:

```
OP_DUP OP_HASH160 9d77f8bcfd56b6a095703aae85bbe003a9cff5eb OP_EQUALVERIFY OP_CHECKSIG
```

The HASH160 fingerprint uniquely identifies the public key whose address we
need. Because this is a standard legacy (P2PKH) script, the solution is to
prepend the mainnet version byte (`0x00`), compute the double-SHA256 checksum,
and Base58Check encode the result.

Run the helper script that was added in `scripts/solve_puzzle256.py`:

```bash
python scripts/solve_puzzle256.py 9d77f8bcfd56b6a095703aae85bbe003a9cff5eb
```

Output:

```
1FMcotmnqqE5M2x9DDX3VfPAPuBWArGisa
```

This fills in the missing middle of the puzzle string `1FMcotmnq-uBWArGisa` and
confirms that the recovered address satisfies the supplied locking script.
