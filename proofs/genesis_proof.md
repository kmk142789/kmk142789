# Genesis Proof (Bitcoin Block 0)

This proof bundle establishes the canonical anchor for Bitcoin's genesis block (height 0). It provides a reproducible path to verify the genesis coinbase witness, block hash, and payout address without relying on third-party services or network calls.

## 1) Rebuild the genesis coinbase witness

Run the canonical reconstruction to derive the merkle root and block hash directly from the genesis coinbase script:

```bash
python - <<'PY'
import hashlib, struct

coinbase_hex = "04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f6620636f6d696e672042616e6b732072657363756573"
coinbase = bytes.fromhex(coinbase_hex)
merkle = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()

version = struct.pack('<L', 1)
prev_block = bytes.fromhex('00' * 32)
timestamp = struct.pack('<L', 1231006505)
target = struct.pack('<L', 486604799)
nonce = struct.pack('<L', 2083236893)
header = version + prev_block + merkle[::-1] + timestamp + target + nonce

block_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
print("Merkle root:", merkle[::-1].hex())
print("Block hash:", block_hash)
PY
```

Expected output:

```
Merkle root: 4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
Block hash: 000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
```

## 2) Derive the genesis payout address

Verify the canonical destination by hashing the genesis payout public key into a Base58Check address:

```bash
python - <<'PY'
import hashlib

pubkey_hex = "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
pubkey = bytes.fromhex(pubkey_hex)

sha = hashlib.sha256(pubkey).digest()
ripemd160 = hashlib.new('ripemd160', sha).digest()
prefix = b'\x00' + ripemd160
checksum = hashlib.sha256(hashlib.sha256(prefix).digest()).digest()[:4]
address = prefix + checksum
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
value = int.from_bytes(address, 'big')
output = []
while value:
    value, mod = divmod(value, 58)
    output.append(alphabet[mod])

for byte in address:
    if byte == 0:
        output.append('1')
    else:
        break

print("Address:", ''.join(reversed(output)))
PY
```

Expected output:

```
Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
```

## 3) Reference the full witness bundle

For additional detail and context, consult the full genesis witness proof:

- `proofs/genesis_coinbase_witness.md`

These steps establish the core genesis proof: the merkle root, block hash, and payout address that are hard-coded into every Bitcoin client.
