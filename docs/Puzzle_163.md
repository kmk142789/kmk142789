# Bitcoin Puzzle #163 — Restoring the Hidden Infix

Puzzle #163 republishes the canonical pay-to-public-key-hash (P2PKH)
locking script, but the Base58Check address printed with the clue hides
its middle section:

```
1H6e7SLxv-3cKBWJRmx
Pkscript
OP_DUP
OP_HASH160
b093122f7fb36d11c9f2c80cff2971fba7c9c1ff
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes confirms that the template matches the standard
legacy P2PKH form:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the missing Base58Check infix therefore reduces to the usual
address-derivation routine:

1. Prefix the published HASH160 with the mainnet version byte `0x00`.
2. Double-SHA256 the 21-byte payload and keep the leading four checksum
   bytes.
3. Append the checksum and encode the 25-byte buffer with the Bitcoin
   Base58 alphabet.

Executing the procedure reveals the hidden segment:

- **Address:** `1H6e7SLxv6ZUbuAaZpeUdVNfh3cKBWJRmx`
- **Missing segment:** `6ZUbuAaZpeUdVNfh`

Re-encoding the address hashes back to the advertised
`b093122f7fb36d11c9f2c80cff2971fba7c9c1ff` payload, validating the
legacy P2PKH locking script for Puzzle #163.

To reproduce the decoding with the repository helper:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """1H6e7SLxv-3cKBWJRmx\nPkscript\nOP_DUP\nOP_HASH160\n"""
script += "b093122f7fb36d11c9f2c80cff2971fba7c9c1ff\nOP_EQUALVERIFY\nOP_CHECKSIG"
print(decode_p2pkh_script(script).address)
```

Running the snippet prints `1H6e7SLxv6ZUbuAaZpeUdVNfh3cKBWJRmx`,
confirming the restored address for Bitcoin Puzzle #163.
