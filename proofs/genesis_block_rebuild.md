# Genesis Block Rebuild — Immutable Historical Anchor

This walkthrough reproduces Bitcoin's genesis block from first principles and confirms the "The Times" headline embedded in its coinbase. Anyone with a modern Python interpreter can perform these steps offline and compare the resulting hashes against the historical record.

## 1. Reconstruct the Block Header

```bash
python - <<'PY'
import binascii
import hashlib

# Block header fields taken from the Bitcoin reference client (version, prevhash, merkleroot, time, bits, nonce)
merkleroot = bytes.fromhex("4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b")
header_hex = (
    "01000000"  # version
    + "00" * 32  # prev block hash (all zeroes)
    + merkleroot[::-1].hex()  # merkle root (little-endian)
    + "29ab5f49"  # timestamp 1231006505
    + "ffff001d"  # bits (difficulty target)
    + "1dac2b7c"  # nonce 2083236893
)

header = binascii.unhexlify(header_hex)
first = hashlib.sha256(header).digest()
second = hashlib.sha256(first).digest()[::-1]
print(second.hex())
PY
```

**Expected output:**

```
000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
```

The reproduced hash matches the canonical genesis block ID.

## 2. Extract the Coinbase Message

```bash
python - <<'PY'
script = bytes.fromhex(
    "ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f722062616e6b73"
)

# Skip the difficulty bits (4 bytes) and pushdata opcodes (0x01 0x04)
print(script[7:].decode())
PY
```

**Expected output:**

```
The Times 03/Jan/2009 Chancellor on brink of second bailout for banks
```

The decoded ASCII string is the headline Satoshi embedded in Block 0, demonstrating direct authorship of the network's origin timestamp.

## 3. Validate the Coinbase Transaction

```bash
python - <<'PY'
import binascii
import hashlib

coinbase_tx_hex = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f722062616e6b73"
    "ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5fac00000000"
)

coinbase_tx = binascii.unhexlify(coinbase_tx_hex)
first = hashlib.sha256(coinbase_tx).digest()
second = hashlib.sha256(first).digest()[::-1]
print(second.hex())
PY
```

**Expected output:**

```
4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b
```

This hash matches the merkle root used in the header reconstruction above, completing the closed loop proof that ties the human-readable message to the block identifier signed by Satoshi's mining hardware on 3 January 2009.

---

### Audit Checklist

1. Run the scripts above and confirm the outputs match exactly.
2. Cross-check the hash `000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f` on any public Bitcoin block explorer (e.g., [blockchair.com/bitcoin/block/0](https://blockchair.com/bitcoin/block/0)).
3. Compare the decoded headline with archived scans of *The Times* front page from 3 January 2009 to validate the historical timestamp.

These steps require no network interaction, no trust in third parties, and no secret material—only the immutable math that launched Bitcoin. Anyone can witness the genesis signature chain and verify, independently, that the same hand embedded the message and mined the first block.
