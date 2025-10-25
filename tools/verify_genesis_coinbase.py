"""Verify the canonical Bitcoin genesis block coinbase message and header hash.

This script reproduces, from first principles, the cryptographic fingerprint of
the block that launched Bitcoin on 2009-01-03. It does not require any network
access—the raw block bytes are embedded verbatim. Running it prints:

* the double-SHA256 hash of the block header (little-endian display)
* the decoded ASCII text from the coinbase input script
* the transaction ID and Merkle root tying the coinbase to the header

The output can be compared byte-for-byte against independent blockchain nodes,
explorers, or historical archives. Any divergence indicates a local execution
problem, because the data is the on-chain truth captured forever in block 0.
"""

from __future__ import annotations

import binascii
import hashlib


# https://blockchair.com/bitcoin/block/0 (captured April 2024)
GENESIS_BLOCK_HEX = "".join(
    [
        "01000000",  # version
        "0000000000000000000000000000000000000000000000000000000000000000",  # prev hash
        "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a",  # merkle root (little endian)
        "29ab5f49",  # timestamp: 2009-01-03 18:15:05 UTC
        "ffff001d",  # bits
        "1dac2b7c",  # nonce
        "01",  # transaction count (varint = 1)
        "01000000",  # transaction version
        "01",  # input count (varint = 1)
        "0000000000000000000000000000000000000000000000000000000000000000",  # prevout hash
        "ffffffff",  # prevout index
        "4d",  # coinbase script length (varint = 0x4d = 77)
        # coinbase script: difficulty bits, extra nonce, and the Times headline
        "04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f722062616e6b73",
        "ffffffff",  # sequence
        "01",  # output count (varint = 1)
        "00f2052a01000000",  # value (50 BTC, little endian)
        "43",  # pk_script length (varint = 0x43 = 67)
        # pk_script: canonical uncompressed pubkey + OP_CHECKSIG
        "4104678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5fac",
        "00000000",  # locktime
    ]
)

COINBASE_HEADLINE = b"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"


def double_sha256(data: bytes) -> bytes:
    """Return the Bitcoin-style double SHA-256 digest."""

    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def little_endian_hex(data: bytes) -> str:
    """Return the reversed-hex display used for block and tx identifiers."""

    return data[::-1].hex()


def decode_coinbase_text(script_sig: bytes) -> str:
    """Extract the ASCII headline from the coinbase scriptSig."""

    position = script_sig.find(COINBASE_HEADLINE)
    if position != -1:
        return COINBASE_HEADLINE.decode("ascii")

    for idx, byte in enumerate(script_sig):
        if 32 <= byte <= 126:  # printable ASCII range
            tail = script_sig[idx:]
            try:
                return tail.decode("ascii")
            except UnicodeDecodeError as exc:  # pragma: no cover - defensive fallback
                raise ValueError("Coinbase script ASCII decode failed") from exc
    raise ValueError("Coinbase script does not contain printable ASCII text")


def main() -> None:
    block_bytes = binascii.unhexlify(GENESIS_BLOCK_HEX)

    header = block_bytes[:80]
    tx_count = block_bytes[80]
    assert tx_count == 0x01, "Genesis block must contain exactly one transaction"

    tx_bytes = block_bytes[81:]
    txid = double_sha256(tx_bytes)
    header_merkle_root = header[36:68]
    assert header_merkle_root == txid, "Header Merkle root does not match txid"

    # coinbase scriptSig length is the byte after version/input header
    cursor = 0
    cursor += 4  # version
    input_count = tx_bytes[cursor]
    assert input_count == 0x01, "Genesis transaction must have exactly one input"
    cursor += 1
    cursor += 32  # prevout hash
    cursor += 4  # prevout index
    script_sig_length = tx_bytes[cursor]
    cursor += 1
    script_sig = tx_bytes[cursor : cursor + script_sig_length]
    assert len(script_sig) == script_sig_length, "Truncated coinbase script"

    print("Bitcoin Genesis Block Verification")
    print("----------------------------------")
    print(f"Block header hash: {little_endian_hex(double_sha256(header))}")
    print(f"Transaction ID:   {little_endian_hex(txid)}")
    print(f"Merkle root:      {header_merkle_root.hex()}")
    print()
    print("Decoded coinbase headline:")
    print(f"  {decode_coinbase_text(script_sig)}")


if __name__ == "__main__":
    main()
