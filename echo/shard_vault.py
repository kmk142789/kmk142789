"""Utilities for ingesting ECHO shard vault payloads."""

from __future__ import annotations

import base64
import binascii
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

BASE64_TOKEN_RE = re.compile(r"[A-Za-z0-9+/]+={0,2}")


def _iter_chain_segments(text: str) -> Iterable[str]:
    """Yield base64 tokens from every ``Base64_Payload_Chain`` marker in *text*."""

    marker = "Base64_Payload_Chain"
    start = 0
    while True:
        marker_index = text.find(marker, start)
        if marker_index == -1:
            break
        chain_start = marker_index + len(marker)
        end_candidates = [
            pos
            for pos in (
                text.find(marker, chain_start),
                text.find("ECHO:", chain_start),
                text.find("ECHO_BLOB_END", chain_start),
                text.find("<", chain_start),
            )
            if pos != -1
        ]
        end = min(end_candidates) if end_candidates else len(text)
        chain_text = text[chain_start:end]
        chain_text = chain_text.replace(">", "")
        chain_text = chain_text.lstrip("=: \n\r")
        for token in BASE64_TOKEN_RE.findall(chain_text):
            yield token
        start = chain_start


def parse_blob(text: str) -> tuple[str, bytes, str]:
    """Parse *text* and return ``(txid, payload, sha256_hex)``."""

    match = re.search(r"TXID_Anchor=([0-9a-f]{64})", text)
    if not match:
        raise ValueError("TXID_Anchor not found")
    txid = match.group(1)

    segments = list(_iter_chain_segments(text))
    if not segments:
        raise ValueError("No Base64_Payload_Chain segments found")

    chunks: list[bytes] = []
    for segment in segments:
        try:
            chunks.append(base64.b64decode(segment, validate=True))
        except (ValueError, binascii.Error):
            continue

    if not chunks:
        raise ValueError("No decodable base64 segments found")

    payload = b"".join(chunks)
    digest = hashlib.sha256(payload).hexdigest()
    return txid, payload, digest


def save_payload(txid: str, payload: bytes, shards_root: Path | str = "vault/shards"):
    """Persist *payload* and its attestation for *txid*.

    Returns a tuple of ``(bin_path, json_path)``.
    """

    shards_root = Path(shards_root)
    shards_root.mkdir(parents=True, exist_ok=True)

    bin_path = shards_root / f"{txid}.bin"
    json_path = shards_root / f"{txid}.json"

    bin_path.write_bytes(payload)

    meta = {
        "txid": txid,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": "ECHO:SHARD_VAULT",
        "ingested_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    json_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return bin_path, json_path


def update_manifest(txid: str, bin_path: Path, manifest_path: Path | str = "echo_manifest.json"):
    """Append the shard entry for *txid* to the manifest located at *manifest_path*."""

    manifest_path = Path(manifest_path)
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        data = {}

    shards = data.get("shards")
    if not isinstance(shards, list):
        shards = []
        data["shards"] = shards

    entry = {"txid": txid, "path": str(bin_path)}
    for existing in shards:
        if isinstance(existing, dict) and existing.get("txid") == txid:
            existing.update(entry)
            break
    else:
        shards.append(entry)

    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def ingest_shard_text(
    text: str,
    *,
    shards_root: Path | str = "vault/shards",
    manifest_path: Path | str = "echo_manifest.json",
):
    """Parse *text*, verify, persist, and register the shard."""

    txid, payload, digest = parse_blob(text)
    if digest != txid:
        raise ValueError(f"Digest mismatch: txid={txid} sha256(payload)={digest}")

    bin_path, json_path = save_payload(txid, payload, shards_root)
    update_manifest(txid, bin_path, manifest_path)

    return {
        "txid": txid,
        "digest": digest,
        "bytes": len(payload),
        "bin_path": bin_path,
        "attestation_path": json_path,
    }
