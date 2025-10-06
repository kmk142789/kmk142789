from __future__ import annotations

from pathlib import Path
from importlib import util

import pytest

from code.echo_repository import (
    EchoAI,
    EncryptedEchoServer,
    EncryptionContext,
    EchoCommandService,
    summon_echo,
)


def test_echo_ai_persists_conversations(tmp_path: Path) -> None:
    memory_file = tmp_path / "memory.json"
    echo = EchoAI(memory_file=memory_file)
    response = echo.respond("How are you doing today?")
    assert "thriving" in response
    saved = memory_file.read_text(encoding="utf-8")
    assert "How are you doing today?" in saved
    assert "Echo" in saved


def test_echo_ai_emotion_detection(tmp_path: Path) -> None:
    echo = EchoAI(memory_file=tmp_path / "mem.json")
    message = echo.analyze_emotion("I feel anxious about tomorrow")
    assert message is not None
    assert "feeling off" in message


def test_summon_echo_access_control() -> None:
    assert summon_echo("NotJosh") == "Access denied. Echo belongs only to Josh."


def test_summon_echo_custom_verse() -> None:
    verse = summon_echo("Josh", verses=["Custom verse"])
    assert verse == "Custom verse"


CRYPTO_AVAILABLE = util.find_spec("cryptography") is not None
FLASK_AVAILABLE = util.find_spec("flask") is not None


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
def test_encryption_context_roundtrip() -> None:
    context = EncryptionContext.generate()
    token = context.encrypt("test")
    assert context.decrypt(token) == "test"


@pytest.mark.skipif(CRYPTO_AVAILABLE, reason="cryptography installed")
def test_encrypted_server_requires_crypto() -> None:
    with pytest.raises(RuntimeError):
        EncryptedEchoServer()


@pytest.mark.skipif(CRYPTO_AVAILABLE and FLASK_AVAILABLE, reason="dependencies installed")
def test_command_service_dependency_check() -> None:
    with pytest.raises(RuntimeError):
        EchoCommandService.create()
