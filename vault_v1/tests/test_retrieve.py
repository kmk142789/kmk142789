from __future__ import annotations

from io import BytesIO

from vault.services.ingest import ingest_stream
from vault.services.retrieve import retrieve_file


def test_round_trip_integrity():
    cases = [
        b"hello world",
        (bytes(range(256)) * 4096)[:3 * 1024 * 1024 + 123],
        (bytes(range(128)) * 97)[:1579],
    ]

    for data in cases:
        ingest_result = ingest_stream(
            BytesIO(data),
            "blob.bin",
            "application/octet-stream",
            1024 * 1024,
            False,
        )
        retrieved = retrieve_file(ingest_result["cid"])
        output = b"".join(retrieved["chunks"])
        assert output == data
        assert retrieved["metadata"]["chunk_count"] == ingest_result["chunk_count"]
