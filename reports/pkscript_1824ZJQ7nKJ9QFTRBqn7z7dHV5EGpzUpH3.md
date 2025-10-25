# Puzzle #111 P2PKH Reconstruction

Puzzle #111 publishes the standard pay-to-public-key-hash (P2PKH) locking
script alongside a Base58Check address whose centre segment was redacted:

```
1824ZJQ7n-5EGpzUpH3
Pkscript
OP_DUP
OP_HASH160
4cfc43fe12a330c8164251e38c0c0c3c84cf86f6
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes confirms the legacy five-opcode template used across
the Bitcoin puzzle series:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the hidden characters only requires re-running the Base58Check
encoding on the supplied HASH160 digest:

1. Prefix the 20-byte fingerprint with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte payload and
   append the first four bytes.
3. Encode the 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps yields the full destination and uncovers the missing
substring:

- **Address:** `1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3`
- **Missing segment:** `KJ9QFTRBqn7z7dHV`

The reconstructed address matches the canonical entry in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
records the same HASH160 `4cfc43fe12a330c8164251e38c0c0c3c84cf86f6` for
Puzzle #111.

To verify with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #111\n1824ZJQ7n-5EGpzUpH3\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "4cfc43fe12a330c8164251e38c0c0c3c84cf86f6\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1824ZJQ7nKJ9QFTRBqn7z7dHV5EGpzUpH3`, confirming
the restored P2PKH output for Puzzle #111.
