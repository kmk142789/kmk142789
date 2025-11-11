from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from ..models import File, FileChunk, Receipt, SessionLocal, get_engine
from .receipts import build_payload, sign_payload
from .utils import get_storage


def retrieve_file(cid: str, sign_receipt: bool = False) -> dict:
    storage = get_storage()

    with SessionLocal(bind=get_engine()) as session:
        file_record = session.scalar(select(File).where(File.cid == cid))
        if file_record is None:
            raise FileNotFoundError(cid)

        chunk_rows = session.scalars(
            select(FileChunk).where(FileChunk.file_id == file_record.id).order_by(FileChunk.position)
        ).all()

        chunk_hashes = [row.chunk.hash for row in chunk_rows]
        data_chunks = [storage.read_chunk(chunk_hash) for chunk_hash in chunk_hashes]

        receipt_dict = None
        if sign_receipt:
            payload = build_payload(
                cid,
                file_record.total_size,
                file_record.merkle_root,
                receipt_type="retrieve",
            )
            receipt_dict = sign_payload(payload)
            session.add(
                Receipt(
                    file_id=file_record.id,
                    receipt_type="retrieve",
                    payload=receipt_dict["payload"],
                    signature=receipt_dict["signature"],
                )
            )
            session.commit()

    return {
        "metadata": {
            "cid": file_record.cid,
            "filename": file_record.filename,
            "mime_type": file_record.mime_type,
            "total_size": file_record.total_size,
            "chunk_count": file_record.chunk_count,
            "merkle_root": file_record.merkle_root,
        },
        "chunks": data_chunks,
        "chunk_hashes": chunk_hashes,
        "receipt": receipt_dict,
    }


def chunk_stream(chunks: Iterable[bytes]) -> Iterable[bytes]:
    for chunk in chunks:
        yield chunk


__all__ = ["retrieve_file", "chunk_stream"]
