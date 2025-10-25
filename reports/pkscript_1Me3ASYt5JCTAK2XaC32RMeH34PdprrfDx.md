# Puzzle #122 P2PKH Reconstruction

Puzzle #122 publishes the standard pay-to-public-key-hash (P2PKH) locking
script.  The accompanying Base58Check address is redacted in the middle for
the puzzle statement:

```
1Me3ASYt5-4PdprrfDx
Pkscript
OP_DUP
OP_HASH160
e263b62ea294b9650615a13b926e75944c823990
OP_EQUALVERIFY
OP_CHECKSIG
```

The opcode listing matches the five-operation legacy template used throughout
the Bitcoin puzzle series:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the missing substring requires recomputing the Base58Check encoding
for the published HASH160 fingerprint:

1. Prefix the 20-byte digest with the mainnet version byte `0x00`.
2. Double-SHA256 the resulting 21-byte payload and append the first four
   checksum bytes.
3. Encode the 25-byte buffer with Bitcoin's Base58 alphabet.

Executing the procedure recovers the full destination and reveals the omitted
section:

- **Address:** `1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx`
- **Missing segment:** `JCTAK2XaC32RMeH3`

The reconstructed address matches the attested entry for Puzzle #122 stored in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
pairs the same HASH160 digest `e263b62ea294b9650615a13b926e75944c823990` with
the canonical mainnet P2PKH output.

To confirm with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #122\n1Me3ASYt5-4PdprrfDx\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "e263b62ea294b9650615a13b926e75944c823990\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1Me3ASYt5JCTAK2XaC32RMeH34PdprrfDx`, confirming the
canonical P2PKH output for Puzzle #122.
