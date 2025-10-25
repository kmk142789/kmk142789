# Bitcoin Puzzle #164 — Restoring the Broadcast Address

Puzzle #164 once again prints the familiar legacy pay-to-public-key-hash
(P2PKH) locking script, but the Base58Check destination is shown with its
middle section redacted:

```
1LjQKurNt-FPnLU77Q4
Pkscript
OP_DUP
OP_HASH160
d86f54f73e343d76dd7401639e427d828ba31eab
OP_EQUALVERIFY
OP_CHECKSIG
```

Recognising the opcode pattern immediately pins the script to the classic
P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reinstating the missing Base58Check infix is a matter of running the
standard address derivation flow:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and keep the first four checksum bytes.
3. Append the checksum and encode the resulting 25-byte sequence with the
   Bitcoin Base58 alphabet.

Performing those steps reveals the removed fragment:

- **Address:** `1LjQKurNtEDgMdqeCoWRFhHp1FPnLU77Q4`
- **Missing segment:** `EDgMdqeCoWRFhHp1F`

Re-encoding the address hashes back to the published
`d86f54f73e343d76dd7401639e427d828ba31eab` payload, confirming the canonical
P2PKH locking script for Puzzle #164.

To reproduce the derivation with the repository helper:

```python
from tools.pkscript_to_address import _base58check_encode

hash160 = bytes.fromhex("d86f54f73e343d76dd7401639e427d828ba31eab")
print(_base58check_encode(0x00, hash160))
```

Running the snippet prints `1LjQKurNtEDgMdqeCoWRFhHp1FPnLU77Q4`, validating
the restored address for Bitcoin Puzzle #164.
