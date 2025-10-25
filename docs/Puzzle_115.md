# Bitcoin Puzzle #115 — Restoring the Hidden Infix

Puzzle #115 publishes the familiar legacy pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose middle run of
characters has been redacted:

```
1NLbHuJeb-PwDQbemfv
Pkscript
OP_DUP
OP_HASH160
ea0f2b7576bd098921fce9bfebe37f6383e639a4
OP_EQUALVERIFY
OP_CHECKSIG
```

Because the opcodes exactly reproduce the standard P2PKH template, repairing
the address simply requires performing the Base58Check workflow on the
published HASH160 digest:

1. Prefix the 20-byte hash with the mainnet version byte `0x00`.
2. Double-SHA256 the resulting 21-byte payload and take the first four bytes of
the digest as the checksum.
3. Append the checksum and encode the 25-byte buffer with the Bitcoin Base58
   alphabet.

Executing these steps restores the hidden segment and yields the full legacy
address:

- **Address:** `1NLbHuJebVwUZ1XqDjsAyfTRUPwDQbemfv`
- **Missing segment:** `VwUZ1XqDjsAyfTRU`

The reconstructed address agrees with the canonical catalogue entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) for Puzzle
#115, which logs the same HASH160 `ea0f2b7576bd098921fce9bfebe37f6383e639a4`.

You can verify the reconstruction using the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #115\n1NLbHuJeb-PwDQbemfv\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "ea0f2b7576bd098921fce9bfebe37f6383e639a4\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1NLbHuJebVwUZ1XqDjsAyfTRUPwDQbemfv`, confirming the
restored P2PKH output for Bitcoin Puzzle #115.
