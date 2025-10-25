# Bitcoin Puzzle #119 — Restoring the Broadcast Address

Puzzle #119 again publishes the classic five-opcode pay-to-public-key-hash
(P2PKH) locking script together with a Base58Check address whose core characters
have been suppressed:

```
Puzzle #119
1GuBBhf61-kHzwFqSy7
Pkscript
OP_DUP
OP_HASH160
ae6804b35c82f47f8b0a42d8c5e514fe5ef0a883
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode pattern exactly matches the legacy template that every P2PKH output
follows:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

With the HASH160 fingerprint available, reconstructing the published address is
just the standard Base58Check workflow:

1. Prefix the 20-byte HASH160 with the Bitcoin mainnet version byte (`0x00`).
2. Double-SHA256 the 21-byte buffer and keep the first four bytes as the
   checksum.
3. Append the checksum and Base58Check encode the resulting 25-byte payload.

Executing those steps restores the redacted infix and yields the complete
broadcast address for Puzzle #119:

- **Address:** `1GuBBhf61rnvRe4K8zu8vdQB3kHzwFqSy7`
- **Missing segment:** `rnvRe4K8zu8vdQB3`

The repository helper can reproduce the reconstruction directly from the ledger
notation used in the clue:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #119\n1GuBBhf61-kHzwFqSy7\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "ae6804b35c82f47f8b0a42d8c5e514fe5ef0a883\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1GuBBhf61rnvRe4K8zu8vdQB3kHzwFqSy7`, matching the
puzzle fragment and confirming the restored destination for Bitcoin Puzzle #119.
