# PKScript Analysis: 14oFNXucftsHiUMY8uctg6N487riuyXs4h

## Summary
The provided locking script is the canonical pay-to-public-key-hash (P2PKH) template. It duplicates the submitted
public key, hashes it with SHA256 then RIPEMD160, compares the result to the embedded hash160 value
`29a78213caa9eea824acf08022ab9dfc83414f56`, and finally verifies the signature with `OP_CHECKSIG`.

## Details
- **Hash160:** `29a78213caa9eea824acf08022ab9dfc83414f56`
- **Script hex:** `76a91429a78213caa9eea824acf08022ab9dfc83414f5688ac`
- **Address restoration:** The heading that accompanied the script (`14oFNXucf-7riuyXs4h`) keeps the first nine and last
  eight Base58Check characters of the legacy address and replaces the missing middle portion with a hyphen. Reinstating
  the omitted characters (`tsHiUMY8uctg6N48`) reproduces the full Base58Check address
  `14oFNXucftsHiUMY8uctg6N487riuyXs4h`.
- **Sigscript:**
  - Pushes a 0x46-byte element containing a DER-encoded ECDSA signature followed by the sighash flag `0x01`
    (`SIGHASH_ALL`). The signature parses to:
    - `r = 0x5e248babbe1a051a1ad3b7951f0c1acf6c0c8ce9e6b9a9c5274fd3e204e77a`
    - `s = 0x6cc954c8657a9df5a58ad95c8580d5684d0c39f0a5420d323ee0fe72d2c4362d`
  - Pushes a compressed secp256k1 public key `031a746c78f72754e0be046186df8a20cdce5c79b2eda76013c647af08d306e49e`,
    whose hash160 matches the value in the locking script.
- **Witness:** Not present (the spend uses the legacy script path only).

## Verification Snippet
The following Python excerpt reconstructs the address and validates the hashes using only the provided public key.

```
import hashlib

alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(data: bytes) -> str:
    value = int.from_bytes(data, "big")
    out = ""
    while value:
        value, remainder = divmod(value, 58)
        out = alphabet[remainder] + out
    prefix = 0
    for b in data:
        if b == 0:
            prefix += 1
        else:
            break
    return "1" * prefix + out

pubkey = bytes.fromhex("031a746c78f72754e0be046186df8a20cdce5c79b2eda76013c647af08d306e49e")
sha = hashlib.sha256(pubkey).digest()
ripemd = hashlib.new("ripemd160", sha).digest()
address = b"\x00" + ripemd
checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
print(b58encode(address + checksum))
print(ripemd.hex())
```

Running it yields `14oFNXucftsHiUMY8uctg6N487riuyXs4h` and confirms the hash160 value
`29a78213caa9eea824acf08022ab9dfc83414f56`.
