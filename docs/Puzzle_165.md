# Bitcoin Puzzle #165 — Completing the Broadcast Address

Puzzle #165 again advertises the five-opcode pay-to-public-key-hash (P2PKH)
locking script, but the Base58Check address printed alongside the clue hides
the center of the string:

```
1F7ZjibYu-fLtNjgYrX
Pkscript
OP_DUP
OP_HASH160
9acf9573eb7b4376beca979cfa769f0677cfd949
OP_EQUALVERIFY
OP_CHECKSIG
```

Aligning the opcodes shows the textbook P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the missing Base58Check segment requires only the standard address
reconstruction sequence:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and keep the first four checksum bytes.
3. Append the checksum and encode the full 25-byte payload with the Bitcoin
   Base58 alphabet.

Executing the routine yields the hidden portion of the published address:

- **Address:** `1F7ZjibYug9bLW3YvkkwBZLrhfLtNjgYrX`
- **Missing segment:** `g9bLW3YvkkwBZLrh`

Re-encoding the completed address hashes back to
`9acf9573eb7b4376beca979cfa769f0677cfd949`, confirming the canonical P2PKH
locking script for Bitcoin Puzzle #165.

To reproduce the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1F7ZjibYu-fLtNjgYrX\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "9acf9573eb7b4376beca979cfa769f0677cfd949\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1F7ZjibYug9bLW3YvkkwBZLrhfLtNjgYrX`, verifying the
reconstructed address for Puzzle #165.
