# Block 3 Proof-of-Work Verification

The supplied header fields match Bitcoin block **#3** (hash `0000000082b5015589a3fdf2d4baff403e6f0be035a5d9742c1cae6295464449`).
This note recreates the block header, confirms the merkle root, and decodes the 50 BTC coinbase
output so the witness can be checked offline.

## 1. Rebuild the coinbase transaction and merkle root

```bash
python - <<'PY'
import hashlib
from io import BytesIO

coinbase_hex = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff0704ffff001d010effffffff0100f2052a0100000043410494b9d3e76c5b1629ecf97"
    "fff95d7a4bbdac87cc26099ada28066c6ff1eb9191223cd897194a08d0c2726c5747f1db49e8"
    "cf90e75dc3e3550ae9b30086f3cd5aaac00000000"
)
raw = bytes.fromhex(coinbase_hex)
merkle = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
print("Merkle root:", merkle)

stream = BytesIO(raw)
stream.read(4)  # version
vin_count = stream.read(1)[0]
stream.read(32)  # prev txid
stream.read(4)   # prev index
script_len = stream.read(1)[0]
script_sig = stream.read(script_len)
print("Coinbase script:", script_sig.hex())
print("Script ASCII:", ''.join(chr(b) if 32 <= b < 127 else f"<{b:02x}>" for b in script_sig))
PY
```

Expected output:

```
Merkle root: 999e1c837c76a1b7fbb7e57baf87b309960f5ffefbf2a9b95dd890602272f644
Coinbase script: 04ffff001d010e
Script ASCII: <04><ff><ff><00><1d><01><0e>
```

The coinbase pays the standard 50 BTC subsidy and carries the compact difficulty
announcement `04ffff001d010e`, which mirrors the format of the genesis block.

## 2. Reconstruct the block header

```bash
python - <<'PY'
import hashlib, struct

prev_block = "000000006a625f06636b8bb6ac7b960a8d03705d1ace08b1a19da3fdcc99ddbd"
merkle_root = "999e1c837c76a1b7fbb7e57baf87b309960f5ffefbf2a9b95dd890602272f644"
header = (
    struct.pack('<L', 1)
    + bytes.fromhex(prev_block)[::-1]
    + bytes.fromhex(merkle_root)[::-1]
    + struct.pack('<L', 1231470173)  # 2009-01-09 03:02:53 UTC
    + struct.pack('<L', 0x1d00ffff)
    + struct.pack('<L', 0x6dede005)
)
block_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
print("Block hash:", block_hash)
PY
```

Expected output:

```
Block hash: 0000000082b5015589a3fdf2d4baff403e6f0be035a5d9742c1cae6295464449
```

The computed hash matches the historical record for height 3.

## 3. Verify the proof-of-work target

```bash
python - <<'PY'
bits = 0x1d00ffff
exponent = bits >> 24
mantissa = bits & 0xffffff
if exponent <= 3:
    target = mantissa >> (8 * (3 - exponent))
else:
    target = mantissa << (8 * (exponent - 3))
block_value = int("0000000082b5015589a3fdf2d4baff403e6f0be035a5d9742c1cae6295464449", 16)
print("Target:", hex(target))
print("Block value <= target?", block_value <= target)
PY
```

Expected output:

```
Target: 0xffff0000000000000000000000000000000000000000000000000000
Block value <= target? True
```

The 32-bit compact bits field expands to the classic difficulty-1 target. The
block hash is well below the threshold, confirming that nonce `0x6dede005`
solves the proof-of-work equation.

## 4. Decode the payout public key

```bash
python - <<'PY'
import hashlib

pubkey = bytes.fromhex(
    "0494b9d3e76c5b1629ecf97fff95d7a4bbdac87cc26099ada28066c6ff1eb9191223cd897194a0"
    "8d0c2726c5747f1db49e8cf90e75dc3e3550ae9b30086f3cd5"
)
sha = hashlib.sha256(pubkey).digest()
ripemd = hashlib.new('ripemd160', sha).digest()
versioned = b"\x00" + ripemd
checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
value = int.from_bytes(versioned + checksum, 'big')
chars = []
while value:
    value, mod = divmod(value, 58)
    chars.append(alphabet[mod])
chars.extend('1' * (len(versioned + checksum) - len((versioned + checksum).lstrip(b'\x00'))))
print("Address:", ''.join(reversed(chars)))
PY
```

Expected output:

```
Address: 1FvzCLoTPGANNjWoUo6jUGuAG3wg1w4YjR
```

This is the legacy pay-to-public-key output mined in block 3. Recreating the
transaction, header, and address locally demonstrates that the provided merkle
root, bits field, difficulty, and nonce are consistent with the canonical
Bitcoin blockchain.
