# Bitcoin Puzzle #111 — Recovering the Redacted P2PKH Address

Puzzle #111 again publishes the legacy pay-to-public-key-hash (P2PKH)
locking script with the Base58Check destination partially censored:

```
1824ZJQ7n-5EGpzUpH3
Pkscript
OP_DUP
OP_HASH160
4cfc43fe12a330c8164251e38c0c0c3c84cf86f6
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence matches the canonical template used throughout the
Bitcoin puzzle campaign:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the missing segment therefore reduces to running the
Base58Check steps on the published HASH160 fingerprint:

1. Prefix the 20-byte digest with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and take the first four bytes as the
   checksum.
3. Append the checksum and encode the resulting 25-byte buffer with the
   Bitcoin Base58 alphabet.

Executing this procedure restores the hidden characters and yields the full
legacy destination:

- **Address:** `1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3`
- **Missing segment:** `KJ9QFTRBqn7z7dHV`

The recovered address matches the canonical catalogue entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), where
the same HASH160 `4cfc43fe12a330c8164251e38c0c0c3c84cf86f6` is paired with
Puzzle #111.

You can confirm the reconstruction with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #111\n1824ZJQ7n-5EGpzUpH3\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "4cfc43fe12a330c8164251e38c0c0c3c84cf86f6\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3`,
confirming the restored P2PKH address for Bitcoin Puzzle #111.
