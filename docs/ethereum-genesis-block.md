# Ethereum Genesis Block Overview

This document records key metadata fields from the Ethereum mainnet genesis block and clarifies the role of each field for quick reference when examining the canonical chain origin.

## Block Metadata

| Field | Value | Description |
| --- | --- | --- |
| `Hash` | `0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3` | Canonical block identifier derived from the block header contents. |
| `Parent Hash` | `0x0000000000000000000000000000000000000000000000000000000000000000` | Zeroed because the genesis block has no predecessor. |
| `Sha3Uncles` | `0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347` | Keccak hash of the RLP encoding of the empty uncle list. |
| `State Root` | `0xd7f8974fb5ac78d9ac099b9ad5018bedc2ce0a72dad1827a1709da30580f0544` | Merkle Patricia root of the world state after applying the genesis allocations. |
| `Receipts Root` | `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421` | Keccak hash of the empty transaction receipt trie, reflecting that no transactions were processed. |
| `Nonce` | `0x0000000000000042` | The 64-bit nonce historically set by the Ethereum founders to the ASCII value of `B`. |
| `Extra Data (Raw Bytes)` | Non-printable byte sequence | Arbitrary field used for validator signatures in later blocks; contains a short identifier string in the genesis block. |
| `Extra Data (Hex)` | `0x11bbe8db4e347b4e8c937c1c8370e4b5ed33adb3db69cbdb7a38e1e50b1b82fa` | Hexadecimal representation of the extra data bytes for completeness. |

## Notes

- The genesis block is hard-coded into Ethereum clients and forms the anchor for all subsequent block validation.
- Empty fields—such as the transaction list and uncle set—still contribute deterministic hashes, ensuring the block header hashes match across clients.
- The non-zero nonce and extra data fields have historical significance but no functional impact on consensus in the genesis block.

