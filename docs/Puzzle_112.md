# Bitcoin Puzzle #112 — Reconstructing the Broadcast Address

Puzzle #112 publishes the canonical legacy pay-to-public-key-hash (P2PKH)
locking script, but the advertised Base58Check address appears with its core
segment redacted:

```
Puzzle #112
18A7NA9FT-uQxpRtCos
Pkscript
OP_DUP
OP_HASH160
4e81efec43c5195aeca0e3877664330418b8e48e
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode sequence matches the five-operation template that every legacy
P2PKH output follows:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the missing middle section is the standard Base58Check
re-encoding exercise:

1. Prefix the published HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and append the first four checksum bytes.
3. Encode the resulting 25-byte value with Bitcoin's Base58 alphabet.

Executing these steps fills in the redacted substring and restores the
broadcast address for Puzzle #112:

- **Address:** `18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos`
- **Missing segment:** `snJxWgkoFfPAFbQz`

The repository tooling reproduces the reconstruction directly from the
published script:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #112\n18A7NA9FT-uQxpRtCos\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "4e81efec43c5195aeca0e3877664330418b8e48e\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `18A7NA9FTsnJxWgkoFfPAFbQzuQxpRtCos`, confirming the
restored destination for Bitcoin Puzzle #112.
