# Bitcoin Puzzle #254 — Restoring the Broadcast Address

Puzzle #254 once again prints the textbook pay-to-public-key-hash (P2PKH)
locking script, but the published legacy address arrives with its middle
segment removed:

```
1NKkjFvXm-bEvnncyza
Pkscript
OP_DUP
OP_HASH160
e9e6a1ad0ddaf3c372e2e1eae83c8cf9f9163b3a
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode pattern exactly matches the classic P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the missing Base58Check infix only requires the standard
address derivation steps:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and keep the first four checksum bytes.
3. Append the checksum and encode the resulting 25-byte sequence with the
   Bitcoin Base58 alphabet.

Executing those steps reinstates the removed fragment:

- **Address:** `1NKkjFvXmovmjwgUujw655n3BbEvnncyza`
- **Missing segment:** `ovmjwgUujw655n3B`

Re-encoding the restored address hashes back to the published
`e9e6a1ad0ddaf3c372e2e1eae83c8cf9f9163b3a` payload, confirming the canonical
P2PKH locking script for Puzzle #254.

To reproduce the derivation with the repository helper:

```python
from tools.pkscript_to_address import _base58check_encode

hash160 = bytes.fromhex("e9e6a1ad0ddaf3c372e2e1eae83c8cf9f9163b3a")
print(_base58check_encode(0x00, hash160))
```

Running the snippet prints `1NKkjFvXmovmjwgUujw655n3BbEvnncyza`, validating
the restored address for Bitcoin Puzzle #254.
