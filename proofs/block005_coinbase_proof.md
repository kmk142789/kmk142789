# Block 5 Coinbase Reconstruction

This guide reproduces the witness for Bitcoin block #5 and confirms that the
historical payout belongs to `1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu`. The workflow
relies only on public RPC endpoints and locally derived hashes, so it can be run
without trusted binaries.

## 1. Resolve the block hash and download the payload

```bash
curl -s https://blockstream.info/api/block-height/5
curl -s https://blockstream.info/api/block/000000009b7262315dbf071787ad3656097b892abffd1f95a1a022f896f533fc/raw \
  > block5.raw
```

The returned hash `000000009b7262315dbf071787ad3656097b892abffd1f95a1a022f896f533fc`
should match what is baked into the coinbase attestation artifacts.

## 2. Parse the coinbase transaction

The block only includes a single transaction, so decoding the coinbase is
straightforward. The following Python snippet prints the coinbase scriptSig,
the pubkey script, and the derived legacy address.

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib
raw = open('block5.raw', 'rb').read()
stream = BytesIO(raw)

def read_varint(s):
    i = s.read(1)[0]
    if i < 0xfd:
        return i
    if i == 0xfd:
        return int.from_bytes(s.read(2), 'little')
    if i == 0xfe:
        return int.from_bytes(s.read(4), 'little')
    return int.from_bytes(s.read(8), 'little')

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def p2pk_address(script_hex):
    pubkey = bytes.fromhex(script_hex[2:-2])
    h160 = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    payload = b"\x00" + h160
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum
    value = int.from_bytes(data, 'big')
    out = ""
    while value:
        value, mod = divmod(value, 58)
        out = alphabet[mod] + out
    for byte in data:
        if byte == 0:
            out = '1' + out
        else:
            break
    return out

stream.read(80)
read_varint(stream)  # tx count
stream.read(4)
read_varint(stream)  # vin count
stream.read(32 + 4)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)
read_varint(stream)  # vout count
value = stream.read(8)
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print('scriptSig (base64):', base64.b64encode(script_sig).decode())
print('pk_script:', pk_script.hex())
print('derived address:', p2pk_address(pk_script.hex()))
print('value (sat):', int.from_bytes(value, 'little'))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BIA==
pk_script: 410456579536d150fbce94ee62b47db2ca43af0a730a0467ba55c79e2a7ec9ce4ad297e35cdbb8e42a4643a60eef7c9abee2f5822f86b1da242d9c2301c431facfd8ac
derived address: 1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu
value (sat): 5000000000
```

The 50 BTC subsidy, the `04ffff001d0120` scriptSig, and the 67-byte pubkey
match the JSON commitments in `satoshi/puzzle-proofs/`.

## 3. Cross-check the attestation

```bash
jq '.' satoshi/puzzle-proofs/master_attestation.json | grep -n "1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu"
```

Referencing the shared attestation index ensures the reconstructed witness is
consistent with the rest of the repository’s Satoshi puzzle set.
