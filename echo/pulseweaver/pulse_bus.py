"""Cross-repository pulse bus with signing and verification helpers."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Mapping, MutableMapping, Optional, Sequence

import httpx
from pydantic import BaseModel, Field, ValidationError

from echo.crypto.sign import sign, verify

__all__ = ["PulsePayload", "PulseEnvelope", "PulseBus", "PulseOutboxEntry"]


class PulsePayload(BaseModel):
    repo: str
    ref: str
    kind: str = Field(pattern="^(merge|fix|doc|schema)$")
    summary: str
    proof_id: str
    timestamp: datetime


class PulseEnvelope(PulsePayload):
    signature: str
    key_id: str


@dataclass(slots=True)
class PulseOutboxEntry:
    path: Path
    envelope: PulseEnvelope


class PulseBus:
    """Emit and ingest signed pulse messages."""

    def __init__(
        self,
        *,
        state_dir: Path | str = Path("state"),
        key_path: Path | str | None = None,
        signing_key: Mapping[str, str] | None = None,
        known_keys_path: Path | str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._pulses_dir = self._state_dir / "pulses"
        self._outbox_dir = self._pulses_dir / "outbox"
        self._inbox_dir = self._pulses_dir / "inbox"
        self._key_path = Path(key_path) if key_path else None
        self._signing_key = dict(signing_key) if signing_key else None
        self._known_keys_path = (
            Path(known_keys_path) if known_keys_path else self._pulses_dir / "keys.json"
        )
        self._http_client = http_client
        for directory in (self._outbox_dir, self._inbox_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._known_keys = self._load_known_keys()

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------
    def _load_known_keys(self) -> MutableMapping[str, str]:
        if not self._known_keys_path.exists():
            return {}
        try:
            data = json.loads(self._known_keys_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, MutableMapping):
            return {}
        return {str(k): str(v) for k, v in data.items()}

    def _persist_known_keys(self) -> None:
        self._known_keys_path.parent.mkdir(parents=True, exist_ok=True)
        self._known_keys_path.write_text(
            json.dumps(self._known_keys, indent=2, sort_keys=True), encoding="utf-8"
        )

    def register_key(self, key_id: str, public_key: str) -> None:
        self._known_keys[str(key_id)] = str(public_key)
        self._persist_known_keys()

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------
    def emit(
        self,
        repo: str,
        ref: str,
        *,
        kind: str,
        summary: str,
        proof_id: str,
        timestamp: datetime | None = None,
        destinations: Sequence[str] | None = None,
    ) -> PulseOutboxEntry:
        payload = PulsePayload(
            repo=repo,
            ref=ref,
            kind=kind,
            summary=summary,
            proof_id=proof_id,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        signed = self._sign_payload(payload)
        path = self._write_outbox(signed)
        for endpoint in destinations or ():
            self._send(endpoint, signed)
        return PulseOutboxEntry(path=path, envelope=signed)

    def _sign_payload(self, payload: PulsePayload) -> PulseEnvelope:
        payload_dict = payload.model_dump()
        if self._signing_key:
            envelope = sign(
                payload_dict,
                private_key_hex=self._signing_key["private_key"],
                key_id=self._signing_key["key_id"],
            )
        else:
            envelope = sign(payload_dict, key_path=self._key_path)
        return PulseEnvelope(**payload_dict, signature=envelope.signature, key_id=envelope.key_id)

    def _write_outbox(self, envelope: PulseEnvelope) -> Path:
        stamp = envelope.timestamp.isoformat().replace(":", "-")
        path = self._outbox_dir / f"{stamp}-{envelope.proof_id}-{uuid.uuid4()}.json"
        path.write_text(envelope.model_dump_json(indent=2), encoding="utf-8")
        return path

    def _send(self, endpoint: str, envelope: PulseEnvelope) -> None:
        payload = envelope.model_dump(mode="json")
        if not self._http_client:
            with httpx.Client(timeout=5.0) as client:
                client.post(endpoint, json=payload)
        else:
            self._http_client.post(endpoint, json=payload)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest(self, payload: Mapping[str, Any]) -> PulseEnvelope:
        try:
            envelope = PulseEnvelope.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid pulse payload: {exc}") from exc
        if not self._verify_signature(envelope):
            raise ValueError("Signature verification failed")
        self._write_inbox(envelope)
        return envelope

    def _write_inbox(self, envelope: PulseEnvelope) -> Path:
        key = f"{envelope.repo}:{envelope.ref}:{envelope.kind}:{envelope.proof_id}"
        digest = uuid.uuid5(uuid.NAMESPACE_URL, key)
        path = self._inbox_dir / f"{envelope.timestamp.isoformat().replace(':', '-')}-{digest}.json"
        if path.exists():
            return path
        path.write_text(envelope.model_dump_json(indent=2), encoding="utf-8")
        return path

    def _verify_signature(self, envelope: PulseEnvelope) -> bool:
        payload_dict = envelope.model_dump(exclude={"signature", "key_id"})
        public_key = self._known_keys.get(envelope.key_id)
        if public_key is None:
            return False
        return verify(payload_dict, envelope.signature, public_key_hex=public_key)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def list_outbox(self) -> List[PulseOutboxEntry]:
        entries: List[PulseOutboxEntry] = []
        for path in sorted(self._outbox_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entries.append(PulseOutboxEntry(path=path, envelope=PulseEnvelope.model_validate(data)))
        return entries

    def list_inbox(self) -> List[PulseEnvelope]:
        envelopes: List[PulseEnvelope] = []
        for path in sorted(self._inbox_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            envelopes.append(PulseEnvelope.model_validate(data))
        return envelopes


PulseMessage = PulseEnvelope
