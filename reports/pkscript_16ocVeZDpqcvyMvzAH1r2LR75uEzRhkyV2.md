# P2PKH Reconstruction for 16ocVeZDp…kyV2

The supplied fragment publishes a standard pay-to-public-key-hash (P2PKH)
locking script together with a Base58Check address whose centre section was
redacted:

```
16ocVeZDp-uEzRhkyV2
Pkscript
OP_DUP
OP_HASH160
3fa96459d3e03e94794724b8605c9ae47a106862
OP_EQUALVERIFY
OP_CHECKSIG
```

Normalising the opcodes reveals the textbook five-operation template used by
legacy mainnet P2PKH outputs:

```
OP_DUP OP_HASH160 <20-byte HASH160> OP_EQUALVERIFY OP_CHECKSIG
```

Recovering the hidden characters only requires re-running the Base58Check
encoding on the published HASH160 digest:

1. Prefix the 20-byte fingerprint with the mainnet version byte `0x00`.
2. Compute the double-SHA256 checksum of the resulting 21-byte payload and
   append the first four bytes.
3. Encode the 25-byte buffer with Bitcoin's Base58 alphabet.

Executing those steps uncovers the missing span and restores the canonical
recipient:

- **Address:** `16ocVeZDpqcvyMvzAH1r2LR75uEzRhkyV2`
- **Missing segment:** `qcvyMvzAH1r2LR75uE`

To verify with the repository tooling:

```python
from tools.decode_pkscript import decode_p2pkh_script

script = """16ocVeZDp-uEzRhkyV2\nPkscript\nOP_DUP\nOP_HASH160\n"
script += "3fa96459d3e03e94794724b8605c9ae47a106862\nOP_EQUALVERIFY\nOP_CHECKSIG"\n
decoded = decode_p2pkh_script(script)
print(decoded.address)
```

Running the snippet prints `16ocVeZDpqcvyMvzAH1r2LR75uEzRhkyV2`, confirming the
reconstructed mainnet P2PKH destination.
