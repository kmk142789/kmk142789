from __future__ import annotations

from io import BytesIO

from sqlalchemy import select

from vault.hashing import hash_bytes
from vault.models import Chunk, SessionLocal, get_engine
from vault.services.ingest import ingest_stream


def test_deduplicates_shared_chunks(tmp_path):
    chunk_size = 1024
    shared = b"A" * chunk_size
    unique_a = b"B" * chunk_size
    unique_b = b"C" * chunk_size

    ingest_stream(BytesIO(shared + unique_a), "file1.bin", "application/octet-stream", chunk_size, False)
    ingest_stream(BytesIO(shared + unique_b), "file2.bin", "application/octet-stream", chunk_size, False)

    with SessionLocal(bind=get_engine()) as session:
        total_chunks = session.scalars(select(Chunk)).all()

    assert len(total_chunks) < 4  # 2 files * 2 chunks each would be 4 without dedupe
    assert any(chunk.hash == hash_bytes(shared) for chunk in total_chunks)
