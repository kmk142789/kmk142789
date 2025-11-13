# Block 6 Coinbase Reconstruction

A companion to the earlier block attestations, this proof anchors Bitcoin block
#6 and binds the original 50 BTC reward to `1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2a`.
Everything happens locally using reproducible steps.

## 1. Resolve the block header and download raw bytes

```bash
curl -s https://blockstream.info/api/block-height/6
curl -s https://blockstream.info/api/block/000000003031a0e73735690c5a1ff2a4be82553b2a12b776fbd3a215dc8f778d/raw \
  > block6.raw
```

Confirm the returned hash matches the historical chain data before moving on.

## 2. Decode the coinbase transaction

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib
raw = open('block6.raw', 'rb').read()
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
read_varint(stream)
stream.read(4)
read_varint(stream)
stream.read(32 + 4)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)
read_varint(stream)
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
scriptSig (base64): BP//AB0BIw==
pk_script: 410408ce279174b34c077c7b2043e3f3d45a588b85ef4ca466740f848ead7fb498f0a795c982552fdfa41616a7c0333a269d62108588e260fd5a48ac8e4dbf49e2bcac
derived address: 1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2a
value (sat): 5000000000
```

As in the prior blocks, the coinbase uses a bare 67-byte public key and spends
the subsidy to an early adopter’s pay-to-pubkey script.

## 3. Add the finding to the attestations

```bash
jq '.block_coinbase[] | select(.height==6)' satoshi/puzzle-proofs/master_attestation.json
```

The JSON record for block #6 captures the same payout address, which means the
on-chain data and the repository attestations continue to line up perfectly.
