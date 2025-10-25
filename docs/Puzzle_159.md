# Bitcoin Puzzle #159 — Reassembling the Broadcast Address

Puzzle #159 advertises the familiar pay-to-public-key-hash (P2PKH)
locking script along with a hyphenated mainnet address clue:

```
14u4nA5su-ChdMnD9E5
Pkscript
OP_DUP
OP_HASH160
2ac1295b4e54b3f15bb0a99f84018d2082495645
OP_EQUALVERIFY
OP_CH
ECKSIG
```

Repairing the split opcode restores the canonical P2PKH template used by
legacy Bitcoin outputs:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check infix follows the standard
address-derivation steps:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes.
3. Encode the resulting 25-byte value with the Bitcoin Base58 alphabet.

Executing these steps restores the elided middle segment:

- **Address:** `14u4nA5sugaswb6SZgn5av2vuChdMnD9E5`
- **Missing segment:** `gaswb6SZgn5av2vu`

The reconstructed address matches the authoritative entry for
HASH160 `2ac1295b4e54b3f15bb0a99f84018d2082495645` recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """14u4nA5su-ChdMnD9E5\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "2ac1295b4e54b3f15bb0a99f84018d2082495645\nOP_EQUALVERIFY\nOP_CH\nECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `14u4nA5sugaswb6SZgn5av2vuChdMnD9E5`, confirming
the restored address for Puzzle #159.
