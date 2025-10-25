# Bitcoin Puzzle #169 — Restoring the Broadcast Address

Puzzle #169 again publishes the classic five-opcode pay-to-public-key-hash
(P2PKH) locking script, but the Base58Check destination is shown with its
middle section replaced by a dash:

```
1G3uazv67-a2898cvCm
Pkscript
OP_DUP
OP_HASH160
a5169d8bc79e8cc94a36246de6bde7596cc9f4bb
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode pattern is immediately recognisable as the standard P2PKH
template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check infix only requires running the textbook
address derivation steps:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and keep the first four checksum bytes.
3. Append the checksum and encode the resulting 25-byte sequence with the
   Bitcoin Base58 alphabet.

Executing those steps reinstates the removed fragment:

- **Address:** `1G3uazv67BcKRmPFvgvX4ijBTa2898cvCm`
- **Missing segment:** `BcKRmPFvgvX4ijBT`

Re-encoding the restored address hashes back to the published
`a5169d8bc79e8cc94a36246de6bde7596cc9f4bb` payload, confirming the canonical
P2PKH locking script for Puzzle #169.

To reproduce the derivation with the repository helper:

```python
from tools.pkscript_to_address import _base58check_encode

hash160 = bytes.fromhex("a5169d8bc79e8cc94a36246de6bde7596cc9f4bb")
print(_base58check_encode(0x00, hash160))
```

Running the snippet prints `1G3uazv67BcKRmPFvgvX4ijBTa2898cvCm`, validating
the restored address for Bitcoin Puzzle #169.
