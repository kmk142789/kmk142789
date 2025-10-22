import random
from pathlib import Path

from safe_secret_scanner import generate_findings


def collect_matches(text: str) -> set[str]:
    return {finding.match_type for finding in generate_findings(Path("dummy.txt"), text)}


def test_detects_prefixed_hex_private_key() -> None:
    sample = "api_secret=0x57c9cbe735dd876ca215db0f4e0264f4716a14f546c6f28a1f233dfabebf1fb0"
    matches = collect_matches(sample)
    assert "hex64_private_like" in matches


def test_detects_base58_32_byte_secret() -> None:
    sample = "solana_secret=2SqYVd8GyK7mXZZYeWvDEFPGN7TN4CSouvV6u7EVQoEo"
    matches = collect_matches(sample)
    assert "base58_secret_like" in matches


def test_detects_base58_64_byte_secret() -> None:
    sample = (
        "monero_seed=5XE7HBHkoKfzVJs4g5N71NjEQrus5c5rZ1aBmTe27d99XEKe3syBrmkSCMzF4adkeu16QP88PmLcCjSrQWFFoz5M"
    )
    matches = collect_matches(sample)
    assert "base58_secret_like" in matches


def test_detects_ethereum_address_like() -> None:
    sample = "public_address=0x3E6034FE5C57292BbC878eAc56F71B1FC2c749d0"
    matches = collect_matches(sample)
    assert "ethereum_address_like" in matches


def test_detects_secret_extended_key() -> None:
    sample = (
        "secret-extended-key-main1qw28gep6kyvqpqx0pvzradryzjurl47qapupqv4ute9xx2tr7vm77s3y70zwv4dmd3xklef24r5z23fpwxxeer7hse97dyzr2s9gq76tfsd7sh5df7hq6devunw3e0dwf8w36z6eqpcexyqkya79vgcjkamjg4ze76egmmsdkm2xw37jkzja6lh82rctsugcjpasu9m3pd6al5axhcdaw8nx5f3jcv37nwyn6wm6vz55gmrfkg9t24l8t3xg4cgpelj0nq004ctmr5q8ql37u"
    )
    matches = collect_matches(sample)
    assert "secret_extended_key" in matches


def test_detects_generated_secret_extended_keys() -> None:
    alphabet = "023456789acdefghjklmnpqrstuvwxyz"
    rng = random.Random(0)

    for length in (82, 96, 128):
        generated = "secret-extended-key-main1" + "".join(rng.choice(alphabet) for _ in range(length))
        matches = collect_matches(generated)
        assert "secret_extended_key" in matches
