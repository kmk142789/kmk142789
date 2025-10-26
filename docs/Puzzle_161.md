# Bitcoin Puzzle #161 — Restoring the Hidden Address Core

Puzzle #161 again presents a familiar pay-to-public-key-hash (P2PKH) locking
script, but the published Base58Check address is missing its centre
segment:

```
1K6k9Aagqk-uwMQTpcnWL
Pkscript
OP_DUP
OP_HASH160
c6885b24810c868bdbc6fbf9dd80de778246da57
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcode sequence confirms it already matches the canonical
P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Reconstructing the absent portion therefore reduces to the standard
Base58Check procedure:

1. Prefix the 20-byte HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 the resulting 21-byte buffer and take the leading four
   checksum bytes.
3. Append the checksum and encode the 25-byte payload with the Bitcoin
   Base58 alphabet.

For reference, the intermediate buffers look like this:

| Stage | Hex bytes |
|-------|-----------|
| Version + HASH160 | `00c6885b24810c868bdbc6fbf9dd80de778246da57` |
| Double-SHA256     | `42567b61987303634f4895e4d6ae528c6709e52df9ad749bbb937e11d08554a0` |
| Checksum (first 4 bytes) | `42567b61` |
| Final payload     | `00c6885b24810c868bdbc6fbf9dd80de778246da5742567b61` |

Encoding this payload restores the missing infix:

- **Address:** `1K6k9AagqkS8STU4uak8F4fSUwMQTpcnWL`
- **Missing segment:** `S8STU4uak8F4fSUw`

The reconstructed address matches the authoritative entry for HASH160
`c6885b24810c868bdbc6fbf9dd80de778246da57` tracked in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json).

To reproduce the decoding with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1K6k9Aagqk-uwMQTpcnWL\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "c6885b24810c868bdbc6fbf9dd80de778246da57\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1K6k9AagqkS8STU4uak8F4fSUwMQTpcnWL`,
confirming the restored address for Bitcoin Puzzle #161.
