# Analysis of P2PKH Spend for Address 18cBEMRxX-bUNKhL5PX

## Overview
- **Address**: `18cBEMRxX-bUNKhL5PX` (interpreted as a Base58Check-encoded P2PKH address; hyphen assumed to be a delimiter)
- **ScriptPubKey (pkScript)**: `OP_DUP OP_HASH160 536ffa992491508dca0354e52f32a3a7a679a53a OP_EQUALVERIFY OP_CHECKSIG`
- **ScriptSig**: `4730440220377f8e53e6d835dd229e1789bc583ec3a0d6273a95fdf891b37571a6c4e1a02a02201e35aa6aba4c8642bd18d3d13ce66cda71030ec69734013a373effabb6a13d840121031277e88390c528ef8efac312d77d0566f756ed54046b8ba557a15b088b86e20b`
- **Witness**: _Not present_ (legacy P2PKH inputs do not carry a witness stack.)

## Decoded Components
- **Public key** (`03 1277… e20b`): 33-byte compressed SECP256k1 key.
- **Signature**: DER-encoded ECDSA signature with SIGHASH flag `0x01` (`SIGHASH_ALL`).

The signature decodes to:
- **r** = `0x377f8e53e6d835dd229e1789bc583ec3a0d6273a95fdf891b37571a6c4e1a02a`
- **s** = `0x1e35aa6aba4c8642bd18d3d13ce66cda71030ec69734013a373effabb6a13d84`

## Validation Check
Hashing the provided public key with SHA-256 followed by RIPEMD-160 produces:
```
536ffa992491508dca0354e52f32a3a7a679a53a
```
This matches the hash160 embedded in the pkScript, confirming that the ScriptSig correctly spends the output.

## Notes
- Because this is a pre-SegWit P2PKH spend, the witness stack is empty. Any reference to a witness for this input should be treated as informational only.
- The hyphen in the supplied address was interpreted as a separator and removed when validating the Base58Check form.
