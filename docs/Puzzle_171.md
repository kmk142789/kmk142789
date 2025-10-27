# Bitcoin Puzzle #171 — Reassembling the Broadcast Address

Puzzle #171 again publishes the standard pay-to-public-key-hash (P2PKH)
locking script, but censors the middle of the legacy Base58Check address:

```
1aaRguU1u-CSvELV1xa
Pkscript
OP_DUP
OP_HASH160
0659a10acba837f71af2129690947e417b9cdca1
OP_EQUALVERIFY
OP_CHECKSIG
```

Removing the artificial line break shows that the opcode sequence already
matches the canonical five-opcode P2PKH template:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

With the script normalised, restoring the redacted portion of the address
reduces to the usual Base58Check workflow:

1. Prefix the published HASH160 with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and retain the
   first four bytes.
3. Append the checksum and encode the 25-byte payload with the Bitcoin
   Base58 alphabet.

For reference, the intermediate buffers are:

| Stage | Hex bytes |
|-------|-----------|
| Version + HASH160 | `000659a10acba837f71af2129690947e417b9cdca1` |
| Double-SHA256     | `90404f073347b0916687b533f75c8d69b992e241e204583ac747d56893ac95b9` |
| Checksum (first 4 bytes) | `90404f07` |
| Final payload     | `000659a10acba837f71af2129690947e417b9cdca190404f07` |

Encoding this payload reinstates the missing infix and recovers the
broadcast destination:

- **Address:** `1aaRguU1ufUKBZUvRu7SDk3mCSvELV1xa`
- **Missing segment:** `ufUKBZUvRu7SDk3m`

The reconstructed address agrees with the authoritative catalogue once the
HASH160 `0659a10acba837f71af2129690947e417b9cdca1` is expanded to its
Base58Check form.

Validate the recovery locally with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1aaRguU1u-CSvELV1xa\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "0659a10acba837f71af2129690947e417b9cdca1\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1aaRguU1ufUKBZUvRu7SDk3mCSvELV1xa`, confirming
the restored address for Bitcoin Puzzle #171.
