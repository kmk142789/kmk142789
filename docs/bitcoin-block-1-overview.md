# Bitcoin Block 1 Overview

This document captures the canonical metadata for Bitcoin's first mined block after the genesis block (height 1). It serves as a quick-reference companion to the repository's broader genesis proofs and highlights the exact header values that every full node validates.

## Block Header Fields

| Field | Value | Description |
| --- | --- | --- |
| `Height` | `1` | First block mined after the genesis block.
| `Hash` | `00000000839a8e6886ab5951d76f411475428afc90947ee320161bbf18eb6048` | Double-SHA256 digest of the block header.
| `Version` | `0x00000001` | Indicates the original Bitcoin block format.
| `Previous Block Hash` | `000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f` | Links back to the hard-coded genesis block.
| `Merkle Root` | `0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098` | Aggregates the lone coinbase transaction included in the block.
| `Timestamp` | `1231469665` (`2009-01-09 02:54:25 UTC`) | Header time recorded when the block was mined.
| `Bits` | `0x1d00ffff` | Encoded proof-of-work difficulty target inherited from genesis.
| `Difficulty` | `1` | Relative difficulty value corresponding to the encoded bits.
| `Nonce` | `0x9962e301` | 32-bit nonce that satisfied the proof-of-work target.

## Notes

- The block contains a single coinbase transaction that pays 50 BTC to the same public key as the genesis reward, preserving early chain continuity.
- Because the header difficulty matches the genesis block, both blocks validate against the same highest possible target (`0x1d00ffff`).
- Block explorers conventionally display the Merkle root in big-endian order; miners serialize it little-endian in the block header. The value above matches the widely published big-endian form for clarity.
