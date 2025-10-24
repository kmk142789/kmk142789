# Bitcoin Puzzle #95 — Repairing the Split Checksig

Puzzle #95 in the Bitcoin puzzle catalogue again surfaces a legacy
pay-to-public-key-hash (P2PKH) locking script with a fractured final
opcode and a hyphenated address hint:

```
19eVSDuiz-KsHdSwoQC
Pkscript
OP_DUP
OP_HASH160
5ed822125365274262191d2b77e88d436dd56d88
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Reuniting the split opcode restores the canonical P2PKH template used by
standard Bitcoin addresses:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

From here the missing address infix follows directly from the Base58Check
encoding process:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

Executing these steps restores the elided middle segment:

- **Address:** `19eVSDuizydXxhohGh8Ki9WY9KsHdSwoQC`
- **Missing segment:** `ydXxhohGh8Ki9WY9`

The reconstructed address matches the authoritative entry for
HASH160 `5ed822125365274262191d2b77e88d436dd56d88` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """19eVSDuiz-KsHdSwoQC\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "5ed822125365274262191d2b77e88d436dd56d88\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `19eVSDuizydXxhohGh8Ki9WY9KsHdSwoQC`, confirming
the restored address for Puzzle #95.
