"""Tests for the identity bridge ASGI application helpers."""

from __future__ import annotations

import importlib

bridge_app_module = importlib.import_module("identity_bridge.app")


def _reset_bridge_cache() -> None:
    """Reset the cached bridge factory to pick up new environment values."""

    bridge_app_module._build_bridge_api.cache_clear()  # type: ignore[attr-defined]


def test_bridge_app_includes_kafka_and_s3(monkeypatch) -> None:
    """Ensure the ASGI bridge factory wires in Kafka and S3 config."""

    monkeypatch.setenv("ECHO_BRIDGE_KAFKA_TOPIC", "echo-kafka")
    monkeypatch.setenv(
        "ECHO_BRIDGE_KAFKA_BOOTSTRAP_SERVERS",
        "kafka-1:9092, kafka-2:9092",
    )
    monkeypatch.setenv("ECHO_BRIDGE_KAFKA_SECRET", "KAFKA_SECRET_NAME")
    monkeypatch.setenv("ECHO_BRIDGE_S3_BUCKET", "echo-bucket")
    monkeypatch.setenv("ECHO_BRIDGE_S3_PREFIX", "artifacts/")
    monkeypatch.setenv("ECHO_BRIDGE_S3_REGION", "us-east-1")
    monkeypatch.setenv("ECHO_BRIDGE_S3_SECRET", "S3_SECRET_NAME")

    importlib.reload(bridge_app_module)
    _reset_bridge_cache()
    api = bridge_app_module._build_bridge_api()

    assert api.kafka_topic == "echo-kafka"
    assert api.kafka_bootstrap_servers == ("kafka-1:9092", "kafka-2:9092")
    assert api.kafka_secret_name == "KAFKA_SECRET_NAME"
    assert api.s3_bucket == "echo-bucket"
    assert api.s3_prefix == "artifacts/"
    assert api.s3_region == "us-east-1"
    assert api.s3_secret_name == "S3_SECRET_NAME"

