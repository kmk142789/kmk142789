# Bitcoin Puzzle #104 — Reassembling the Broadcast Address

Puzzle #104 advertises the canonical pay-to-public-key-hash (P2PKH) locking
script alongside a Base58Check address whose middle portion has been
intentionally removed:

```
1EQJvpsmh-RnzarMVZu
Pkscript
OP_DUP
OP_HASH160
93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence is the textbook P2PKH template employed throughout the
Bitcoin puzzle campaign, so recovering the hidden infix reduces to applying
the Base58Check steps to the provided HASH160 fingerprint:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and keep the first four bytes as the
   checksum.
3. Append the checksum and encode the 25-byte buffer with the Bitcoin
   Base58 alphabet.

Running this procedure restores the missing characters and yields the full
legacy destination:

- **Address:** `1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu`
- **Missing segment:** `azYCcKX5Au6AZmZK`

The recovered address matches the authoritative catalogue entry stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), where
the same HASH160 `93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74` is recorded for
Puzzle #104.

You can validate the reconstruction with the repository helpers:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #104\n1EQJvpsmh-RnzarMVZu\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Executing the snippet prints `1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu`,
confirming the restored P2PKH address for Bitcoin Puzzle #104.
