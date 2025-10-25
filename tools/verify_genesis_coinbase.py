"""Verify the canonical Bitcoin genesis block coinbase message and header hash.

This script reproduces, from first principles, the cryptographic fingerprint of
the block that launched Bitcoin on 2009-01-03. It does not require any network
access—the raw block bytes are embedded verbatim. Running it prints:

* the double-SHA256 hash of the block header (little-endian display)
* the decoded ASCII text from the coinbase input script
* the transaction ID and Merkle root tying the coinbase to the header
* the proof-of-work target check derived from the compact ``bits`` field
* the 50 BTC output decoded to Bitcoin's first address ``1A1zP1...``

The output can be compared byte-for-byte against independent blockchain nodes,
explorers, or historical archives. Any divergence indicates a local execution
problem, because the data is the on-chain truth captured forever in block 0.
"""

from __future__ import annotations

import binascii
import hashlib


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


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


def read_varint(buffer: bytes, offset: int) -> tuple[int, int]:
    """Parse a Bitcoin varint and return the value with the new cursor position."""

    prefix = buffer[offset]
    if prefix < 0xFD:
        return prefix, offset + 1
    if prefix == 0xFD:
        return int.from_bytes(buffer[offset + 1 : offset + 3], "little"), offset + 3
    if prefix == 0xFE:
        return int.from_bytes(buffer[offset + 1 : offset + 5], "little"), offset + 5
    return int.from_bytes(buffer[offset + 1 : offset + 9], "little"), offset + 9


def bits_to_target(bits_le: bytes) -> int:
    """Convert the compact difficulty representation into a full target integer."""

    if len(bits_le) != 4:
        raise ValueError("Compact bits field must be exactly 4 bytes")
    bits_value = int.from_bytes(bits_le, "little")
    exponent = bits_value >> 24
    mantissa = bits_value & 0xFFFFFF
    return mantissa * 2 ** (8 * (exponent - 3))


def encode_base58_check(payload: bytes) -> str:
    """Encode bytes using Base58Check (version + payload + checksum)."""

    checksum = double_sha256(payload)[:4]
    data = payload + checksum
    number = int.from_bytes(data, "big")
    encoded = ""
    while number > 0:
        number, remainder = divmod(number, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded
    # Preserve leading zero bytes as alphabet's first symbol.
    leading_zeros = len(data) - len(data.lstrip(b"\x00"))
    return BASE58_ALPHABET[0] * leading_zeros + encoded


def derive_p2pkh_address(pk_script: bytes) -> str:
    """Decode the canonical P2PKH script to the original Bitcoin address."""

    if not pk_script or pk_script[0] != 0x41 or pk_script[-1] != 0xAC:
        raise ValueError("Unexpected genesis pk_script format")
    pubkey = pk_script[1:66]
    if len(pubkey) != 65:
        raise ValueError("Unexpected genesis public key length")
    pubkey_hash = hashlib.new("ripemd160", hashlib.sha256(pubkey).digest()).digest()
    return encode_base58_check(b"\x00" + pubkey_hash)


def format_btc(value_sats: int) -> str:
    """Render satoshis as an 8-decimal BTC string."""

    return f"{value_sats / 100_000_000:.8f}"


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

    cursor = 0
    cursor += 4  # tx version
    input_count, cursor = read_varint(tx_bytes, cursor)
    assert input_count == 0x01, "Genesis transaction must have exactly one input"
    cursor += 32  # prevout hash
    cursor += 4  # prevout index
    script_sig_length, cursor = read_varint(tx_bytes, cursor)
    script_sig = tx_bytes[cursor : cursor + script_sig_length]
    assert len(script_sig) == script_sig_length, "Truncated coinbase script"
    cursor += script_sig_length
    cursor += 4  # sequence
    output_count, cursor = read_varint(tx_bytes, cursor)
    assert output_count == 0x01, "Genesis transaction must have exactly one output"
    value_satoshis = int.from_bytes(tx_bytes[cursor : cursor + 8], "little")
    cursor += 8
    pk_script_length, cursor = read_varint(tx_bytes, cursor)
    pk_script = tx_bytes[cursor : cursor + pk_script_length]
    assert len(pk_script) == pk_script_length, "Truncated pk_script"

    header_hash = double_sha256(header)
    target = bits_to_target(header[72:76])
    hash_int = int.from_bytes(header_hash[::-1], "big")

    print("Bitcoin Genesis Block Verification")
    print("----------------------------------")
    print(f"Block header hash: {little_endian_hex(header_hash)}")
    print(f"Transaction ID:   {little_endian_hex(txid)}")
    print(f"Merkle root:      {header_merkle_root.hex()}")
    print()
    print("Proof-of-work:")
    print(f"  Compact bits:   0x{int.from_bytes(header[72:76], 'little'):08x}")
    print(f"  Target:         {target:064x}")
    print(f"  Hash as int:    {hash_int:064x}")
    print(f"  Meets target:   {hash_int <= target}")
    print()
    print("Coinbase output:")
    print(f"  Value:          {value_satoshis:,} satoshis ({format_btc(value_satoshis)} BTC)")
    print(f"  Recipient:      {derive_p2pkh_address(pk_script)}")
    print()
    print("Decoded coinbase headline:")
    print(f"  {decode_coinbase_text(script_sig)}")


if __name__ == "__main__":
    main()
