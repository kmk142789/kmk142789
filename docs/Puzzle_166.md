# Bitcoin Puzzle #166 — Restoring the Broadcast Address

Puzzle #166 reprises the familiar five-opcode pay-to-public-key-hash (P2PKH)
locking script, but the Base58Check address published alongside the clue drops
its central segment:

```
12BtvPaam-6hMRnASZ4
Pkscript
OP_DUP
OP_HASH160
0d07a05f7687824fb4dd4a160ddbdc3808655004
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence mirrors the textbook P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check characters only requires the standard
address reconstruction flow:

1. Prefix the HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the resulting 21-byte buffer and keep the first four checksum
   bytes.
3. Append the checksum and encode the full 25-byte payload with the Bitcoin
   Base58 alphabet.

Executing the routine restores the redacted center of the address:

- **Address:** `12BtvPaamiBCpXmoDrsCxAa1b6hMRnASZ4`
- **Missing segment:** `iBCpXmoDrsCxAa1b`

Hashing the completed address reproduces the published HASH160
`0d07a05f7687824fb4dd4a160ddbdc3808655004`, confirming the canonical P2PKH
locking script for Bitcoin Puzzle #166.

To re-run the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """12BtvPaam-6hMRnASZ4\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "0d07a05f7687824fb4dd4a160ddbdc3808655004\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `12BtvPaamiBCpXmoDrsCxAa1b6hMRnASZ4`, verifying the
reconstructed address for Puzzle #166.
