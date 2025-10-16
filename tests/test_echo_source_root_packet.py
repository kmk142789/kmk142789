import hashlib

import pytest

from echo_source_root import decode_packet


def test_decode_packet_accepts_missing_padding():
    raw = "IDAmlRtAipuoIPqX+mn88husyppxLtdHuYwFccQwWCLcGyLqIP1eFu7Zur6b6K7Wjai0spx7aKZ82j4PPjlbXic"
    packet = decode_packet(raw)
    assert len(packet) == 65
    assert packet.hex() == (
        "203026951b408a9ba820fa97fa69fcf21bacca9a712ed747b98c0571c4305822dc1b22ea20fd5e16eed9babe"
        "9be8aed68da8b4b29c7b68a67cda3e0f3e395b5e27"
    )
    assert hashlib.sha256(packet).hexdigest() == "a3093176b50f37e35a6b6f8c380c40726e0900d2654e9b7eccd6b6748401b201"


def test_decode_packet_rejects_bad_base64():
    with pytest.raises(ValueError):
        decode_packet("not-base64!!")
