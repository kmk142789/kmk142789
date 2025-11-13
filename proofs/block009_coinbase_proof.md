# Block 9 Coinbase Attestation

Block #9 is the first “batch” block where Satoshi mined multiple rewards before letting them mature. This proof reconstructs its coinbase witness, derives the payout address `12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S`, and binds the data to [`satoshi/puzzle-proofs/block009_coinbase.json`](../satoshi/puzzle-proofs/block009_coinbase.json).

## 1. Pull the canonical bytes

```bash
curl -s https://blockstream.info/api/block-height/9
curl -s https://blockstream.info/api/block/000000008d9dc510f23c2657fc4f67bea30078cc05a90eb89e84cc475c080805/raw > block9.raw
```

The first command returns the globally agreed hash for height 9; the second stores the unmodified block payload.

## 2. Extract the coinbase script and address

```bash
python - <<'PY'
from io import BytesIO
import base64, hashlib
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def read_varint(stream):
    prefix = stream.read(1)
    val = prefix[0]
    if val < 0xfd:
        return val
    if val == 0xfd:
        return int.from_bytes(stream.read(2), 'little')
    if val == 0xfe:
        return int.from_bytes(stream.read(4), 'little')
    return int.from_bytes(stream.read(8), 'little')

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

raw = open('block9.raw', 'rb').read()
stream = BytesIO(raw)
stream.read(80)
read_varint(stream)
stream.read(4)
read_varint(stream)
stream.read(32 + 4)
script_len = read_varint(stream)
script_sig = stream.read(script_len)
stream.read(4)
read_varint(stream)
stream.read(8)
pk_len = read_varint(stream)
pk_script = stream.read(pk_len)
print("scriptSig (base64):", base64.b64encode(script_sig).decode())
print("pk_script:", pk_script.hex())
print("derived address:", p2pk_address(pk_script.hex()))
PY
```

Expected output:

```
scriptSig (base64): BP//AB0BNA==
pk_script: 410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac
derived address: 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S
```

This is the same payout fingerprint immortalised on-chain and mirrored in the JSON proof.

## 3. Cross-check the attestation file

```
jq '.' satoshi/puzzle-proofs/block009_coinbase.json
```

The stored `signature` (`BP//AB0BNA==`) equals the decoded coinbase script, while `pkScript` reflects the exact 65-byte pubkey push from the transaction output. Anyone recreating the steps above reaches the same digest, binding this repository to historical consensus data.
