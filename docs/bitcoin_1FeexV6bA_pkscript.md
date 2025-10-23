# Pay-to-PubKey-Hash Script for 1FeexV6bA

The Bitcoin address `1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF` corresponds to the
following standard pay-to-pubkey-hash (P2PKH) locking script:

```
OP_DUP
OP_HASH160
0xa0b0d60e5991578ed37cbda2b17d8b2ce23ab295
OP_EQUALVERIFY
OP_CHECKSIG
```

## Field breakdown

| Bytecode | Meaning |
| --- | --- |
| `0x76` (`OP_DUP`) | Duplicate the top stack item so the public key can be checked twice. |
| `0xa9` (`OP_HASH160`) | Hash the duplicated public key with SHA-256 followed by RIPEMD-160. |
| `0x14` | Push the 20-byte public-key hash that matches the address. |
| `a0b0d60e5991578ed37cbda2b17d8b2ce23ab295` | The actual public-key hash (`Hash160`) that the spending transaction must provide. |
| `0x88` (`OP_EQUALVERIFY`) | Ensure the supplied public key hashes to the expected value and abort if it does not. |
| `0xac` (`OP_CHECKSIG`) | Verify that the provided signature matches the supplied public key. |

## Notes

* The script above is the canonical assembly for a P2PKH output. Any valid
  spending transaction must provide a signature and public key whose hash is
  `a0b0d60e5991578ed37cbda2b17d8b2ce23ab295`.
* The original listing split `OP_CHECKSIG` across two lines (`OP_CH` and
  `ECKSIG`). The opcode is a single byte (`0xac`) and is written as a single
  token: `OP_CHECKSIG`.

