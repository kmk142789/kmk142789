# Bitcoin Puzzle #162 — Restoring the Broadcast Address

Puzzle #162 again publishes the classic pay-to-public-key-hash (P2PKH)
locking script, but the Base58Check address that accompanies the clue is
shown with its middle section excised:

```
17DTUTXUc-Lrs1xMnS2
Pkscript
OP_DUP
OP_HASH160
442bd85a46d4acd7b082c1d731fb13c8474ffa6f
OP_EQUALVERIFY
OP_CHECKSIG
```

Once the opcodes are lined up, the template matches the legacy P2PKH
form exactly:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check infix requires only the standard
address-derivation steps:

1. Prefix the 20-byte HASH160 payload with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte buffer and take the first four checksum bytes.
3. Append the checksum and encode the 25-byte payload with the Bitcoin
   Base58 alphabet.

Carrying out the procedure reveals the hidden segment:

- **Address:** `17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2`
- **Missing segment:** `UYEgrr5GhivxYei4`

Re-encoding the address confirms that it hashes back to the provided
`442bd85a46d4acd7b082c1d731fb13c8474ffa6f` payload, validating the
canonical P2PKH locking script.

To reproduce the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """17DTUTXUc-Lrs1xMnS2\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "442bd85a46d4acd7b082c1d731fb13c8474ffa6f\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2`, confirming
the restored address for Bitcoin Puzzle #162.
