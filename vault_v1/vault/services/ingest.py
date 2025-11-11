from __future__ import annotations

from io import BufferedReader, BytesIO
from typing import BinaryIO, Iterable

from sqlalchemy import select

from ..hashing import compute_merkle_root, hash_bytes, hash_concat
from ..models import Chunk, File, FileChunk, Receipt, SessionLocal, get_engine
from .receipts import build_payload, sign_payload
from .utils import get_storage


def _iter_chunks(stream: BinaryIO, chunk_size: int) -> Iterable[bytes]:
    while True:
        data = stream.read(chunk_size)
        if not data:
            break
        yield data


def _ensure_buffer(stream: BinaryIO) -> BinaryIO:
    if isinstance(stream, (BufferedReader, BytesIO)):
        return stream
    if hasattr(stream, "buffer"):
        return stream.buffer
    return BytesIO(stream.read())


def ingest_stream(
    stream: BinaryIO,
    filename: str | None,
    mime_type: str | None,
    chunk_size: int,
    sign_receipt: bool,
    uploader: str | None = None,
) -> dict:
    storage = get_storage()
    stream = _ensure_buffer(stream)

    chunk_hashes: list[str] = []
    total_size = 0

    with SessionLocal(bind=get_engine()) as session:
        chunk_models: list[Chunk] = []

        for chunk in _iter_chunks(stream, chunk_size):
            total_size += len(chunk)
            chunk_hash = hash_bytes(chunk)
            chunk_hashes.append(chunk_hash)

            existing_chunk = session.scalar(select(Chunk).where(Chunk.hash == chunk_hash))
            if existing_chunk is None:
                storage.write_chunk(chunk_hash, chunk)
                existing_chunk = Chunk(hash=chunk_hash, size=len(chunk))
                session.add(existing_chunk)
                session.flush()

            chunk_models.append(existing_chunk)

        if not chunk_hashes:
            empty_hash = hash_bytes(b"")
            chunk_hashes.append(empty_hash)
            storage.write_chunk(empty_hash, b"")
            existing_chunk = session.scalar(select(Chunk).where(Chunk.hash == empty_hash))
            if existing_chunk is None:
                existing_chunk = Chunk(hash=empty_hash, size=0)
                session.add(existing_chunk)
                session.flush()
            chunk_models.append(existing_chunk)

        cid = hash_concat(chunk_hashes)
        merkle_root = compute_merkle_root(chunk_hashes)

        file_record = File(
            cid=cid,
            filename=filename,
            mime_type=mime_type,
            uploader=uploader,
            total_size=total_size,
            chunk_count=len(chunk_hashes),
            merkle_root=merkle_root,
        )
        session.add(file_record)
        session.flush()

        for index, chunk_model in enumerate(chunk_models):
            session.add(
                FileChunk(
                    file_id=file_record.id,
                    chunk_id=chunk_model.id,
                    position=index,
                )
            )

        receipt_dict = None
        if sign_receipt:
            payload = build_payload(cid, total_size, merkle_root, receipt_type="ingest")
            receipt_dict = sign_payload(payload)
            session.add(
                Receipt(
                    file_id=file_record.id,
                    receipt_type="ingest",
                    payload=receipt_dict["payload"],
                    signature=receipt_dict["signature"],
                )
            )

        session.commit()

    return {
        "cid": cid,
        "total_size": total_size,
        "chunk_count": len(chunk_hashes),
        "merkle_root": merkle_root,
        "receipt": receipt_dict,
    }
