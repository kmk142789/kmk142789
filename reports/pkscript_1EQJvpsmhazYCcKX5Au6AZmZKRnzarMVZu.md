# Puzzle #104 P2PKH Reconstruction

Puzzle #104 publishes the familiar pay-to-public-key-hash (P2PKH) locking
script with the advertised Base58Check address missing its middle segment:

```
1EQJvpsmh-RnzarMVZu
Pkscript
OP_DUP
OP_HASH160
93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes confirms the legacy template used across the
Bitcoin puzzle series:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Restoring the redacted portion follows the standard Base58Check procedure
for deriving a mainnet P2PKH address from the supplied HASH160 payload:

1. Prefix the 20-byte fingerprint with the version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte payload and
   append the first four bytes.
3. Encode the 25-byte buffer with the Bitcoin Base58 alphabet.

Executing these steps yields the complete destination and reveals the
removed substring:

- **Address:** `1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu`
- **Missing segment:** `azYCcKX5Au6AZmZK`

The reconstructed address matches the attested entry recorded in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json), which
pairs HASH160 `93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74` with the same
mainnet P2PKH output for Puzzle #104.

To verify with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """Puzzle #104\n1EQJvpsmh-RnzarMVZu\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "93022af9a38f3ebb0c3f15dd1c83f8fadaf64e74\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_pkscript.decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `1EQJvpsmhazYCcKX5Au6AZmZKRnzarMVZu`, confirming
the restored P2PKH address for Puzzle #104.
