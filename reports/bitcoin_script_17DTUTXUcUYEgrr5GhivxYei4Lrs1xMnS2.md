# Bitcoin Script Breakdown for 17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2

## Overview
- **Address type:** Legacy pay-to-public-key-hash (P2PKH).
- **Locking script (scriptPubKey):**
  ```
  OP_DUP OP_HASH160 442bd85a46d4acd7b082c1d731fb13c8474ffa6f OP_EQUALVERIFY OP_CHECKSIG
  ```
- The 20-byte hash `442bd85a46d4acd7b082c1d731fb13c8474ffa6f` is the RIPEMD-160 hash of the compressed public key shown in the unlocking script.
- Encoding that hash with the mainnet prefix (`0x00`) yields the Base58Check address **17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2**.

## Unlocking script (scriptSig)
The provided `scriptSig` is:
```
473044022040d5ec7eb54900e560cac0912b5a08f339636a9cba2bf778a7ff8c780abae5220220263c238cfba6144c824307f3662827e2b3b620cbfabf0a0152ad7ba8de73eb8c012103294d33f5e7b98c885ff540fd3f747010999f640d8fdb021f5a13ef3d06c36a58
```
Breaking this down:
- `0x47` – length of the DER-encoded signature (71 bytes).
- Signature DER structure:
  - `0x30` – DER sequence marker.
  - `0x44` – sequence length (68 bytes following this byte).
  - `0x02 0x20` – first integer (`r`) has length 32 bytes.
    - `r = 0x40d5ec7eb54900e560cac0912b5a08f339636a9cba2bf778a7ff8c780abae522`
  - `0x02 0x20` – second integer (`s`) has length 32 bytes.
    - `s = 0x263c238cfba6144c824307f3662827e2b3b620cbfabf0a0152ad7ba8de73eb8c`
  - The final byte `0x01` outside the DER structure is the SIGHASH flag, indicating **SIGHASH_ALL**.
- `0x21` – length of the public key (33 bytes), confirming it is compressed.
  - Public key: `03294d33f5e7b98c885ff540fd3f747010999f640d8fdb021f5a13ef3d06c36a58`
    - Begins with `0x03`, so the y-coordinate is odd.

## Witness data
- No SegWit witness data is present. This is expected for legacy P2PKH spends; the witness section is empty.

## Validation steps
1. Hashing the 33-byte public key with SHA-256 followed by RIPEMD-160 gives `442bd85a46d4acd7b082c1d731fb13c8474ffa6f`.
2. Embedding that hash into the standard P2PKH locking script produces the `scriptPubKey` shown above.
3. Base58Check-encoding the version-prefixed hash reproduces the Bitcoin mainnet address `17DTUTXUcUYEgrr5GhivxYei4Lrs1xMnS2`, confirming the script and unlocking data are consistent.
