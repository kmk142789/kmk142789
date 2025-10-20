"""FastAPI endpoint scaffolding for decoding living glyph scans."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from nacl import signing
from nacl.exceptions import BadSignatureError

from .memory_hash_feed import MemoryHashFeed

logger = logging.getLogger(__name__)


class ScanPayload(BaseModel):
    encoded: str
    signature: str


class DecodedResponse(BaseModel):
    snapshot: Dict[str, Any]
    valid: bool


@dataclass(slots=True)
class ScanDecoder:
    """Validate signed payloads and surface the *current* Echo context."""

    verifier: signing.VerifyKey
    feed: MemoryHashFeed

    def decode(self, payload: ScanPayload) -> DecodedResponse:
        try:
            message = bytes.fromhex(payload.encoded)
            signature = bytes.fromhex(payload.signature)
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail="Invalid hex payload") from exc

        try:
            self.verifier.verify(message, signature)
        except BadSignatureError as exc:
            logger.warning("Invalid signature supplied for living glyph scan")
            raise HTTPException(status_code=403, detail="Invalid signature") from exc

        extra_context = json.loads(message.decode("utf-8"))
        snapshot = self.feed.build_snapshot(extra_context=extra_context)
        return DecodedResponse(snapshot=snapshot, valid=True)


def create_app(decoder: ScanDecoder) -> FastAPI:
    app = FastAPI(title="Echo Living Glyph Scan Decoder")

    @app.post("/scan", response_model=DecodedResponse)
    def scan_endpoint(payload: ScanPayload, service: ScanDecoder = Depends(lambda: decoder)) -> DecodedResponse:
        return service.decode(payload)

    return app


def build_decoder(hex_public_key: str, feed: MemoryHashFeed | None = None) -> ScanDecoder:
    verifier = signing.VerifyKey(bytes.fromhex(hex_public_key))
    feed = feed or MemoryHashFeed()
    return ScanDecoder(verifier=verifier, feed=feed)


__all__ = ["ScanDecoder", "create_app", "build_decoder", "ScanPayload", "DecodedResponse"]

