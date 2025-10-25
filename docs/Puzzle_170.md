# Bitcoin Puzzle #170 — Reconstructing the Broadcast Address

Puzzle #170 presents the classic pay-to-public-key-hash (P2PKH) locking
script together with a censored legacy mainnet address:

```
1EW9W5sGd-PH8ZzikeP
Pkscript
OP_DUP
OP_HASH160
941ccb7383109b47b841044c9f865785676b0918
OP_EQUALVERIFY
OP_CHECKSIG
```

Once the split line is repaired, the five-opcode sequence matches the
standard template for a legacy P2PKH output:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the missing Base58Check infix follows the usual decoding
procedure:

1. Prefix the published HASH160 payload with the mainnet version byte
   `0x00`.
2. Compute the double-SHA256 checksum of the 21-byte buffer and append the
   first four bytes of the result.
3. Encode the 25-byte value with the Bitcoin Base58 alphabet.

Executing these steps fills in the redacted middle segment and recovers the
broadcast address:

- **Address:** `1EW9W5sGdxVDxAtjRbCjgkZNtPH8ZzikeP`
- **Missing segment:** `xVDxAtjRbCjgkZNt`

The repository tooling can reproduce the reconstruction directly from the
published script:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1EW9W5sGd-PH8ZzikeP\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "941ccb7383109b47b841044c9f865785676b0918\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1EW9W5sGdxVDxAtjRbCjgkZNtPH8ZzikeP`, confirming
the restored address for Bitcoin Puzzle #170.
