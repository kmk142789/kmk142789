from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..config import get_settings
from ..hashing import compute_merkle_root
from ..services.ingest import ingest_stream
from ..services.retrieve import chunk_stream, retrieve_file

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    chunk_size: int | None = None,
    sign: bool = False,
):
    settings = get_settings()
    chosen_chunk_size = chunk_size or settings.default_chunk_size
    if chosen_chunk_size <= 0:
        raise HTTPException(status_code=400, detail="chunk_size must be positive")

    result = ingest_stream(
        stream=file.file,
        filename=file.filename,
        mime_type=file.content_type,
        chunk_size=chosen_chunk_size,
        sign_receipt=sign,
        uploader="api",
    )
    return result


@router.get("/{cid}")
async def download_file(cid: str):
    try:
        result = retrieve_file(cid, sign_receipt=False)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found") from None

    media_type = result["metadata"].get("mime_type") or "application/octet-stream"
    filename = result["metadata"].get("filename")

    headers = {}
    if filename:
        headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""

    return StreamingResponse(chunk_stream(result["chunks"]), media_type=media_type, headers=headers)


@router.get("/{cid}/proof")
async def get_proof(cid: str, sign: bool = False):
    try:
        result = retrieve_file(cid, sign_receipt=sign)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found") from None

    proof = {
        "cid": result["metadata"]["cid"],
        "merkle_root": result["metadata"]["merkle_root"],
        "chunk_hashes": result["chunk_hashes"],
    }
    if sign:
        proof["receipt"] = result["receipt"]

    # defensive recompute
    recomputed_root = compute_merkle_root(result["chunk_hashes"])
    proof["verified"] = proof["merkle_root"] == recomputed_root
    return proof


__all__ = ["router"]
