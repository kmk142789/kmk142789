"""Fractal Keysmith utilities for validating attestations."""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import List, Optional


_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


@dataclass(frozen=True)
class TranscriptLine:
    action: str
    detail: str
    status: str


@dataclass(frozen=True)
class KeyAttestation:
    key: Optional[str]
    valid: bool
    repaired: bool
    transcript: List[TranscriptLine]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "valid": self.valid,
            "repaired": self.repaired,
            "transcript": [line.__dict__ for line in self.transcript],
        }


class FractalKeysmith:
    """Validate and repair fractal keys while keeping transcripts."""

    def __init__(self) -> None:
        self._cache: dict[str, KeyAttestation] = {}

    def _record(self, transcript: List[TranscriptLine], action: str, detail: str, status: str) -> None:
        transcript.append(TranscriptLine(action=action, detail=detail, status=status))

    def _load_raw(self, source: str, transcript: List[TranscriptLine]) -> str:
        path = pathlib.Path(source)
        if path.exists():
            raw = path.read_text(encoding="utf-8").strip()
            self._record(transcript, "load", f"file:{path}", "ok")
            return raw
        self._record(transcript, "load", "inline", "ok")
        return source.strip()

    def _normalize(self, raw: str, transcript: List[TranscriptLine]) -> str:
        cleaned = raw.strip().replace(" ", "").replace("-", "").replace("\n", "")
        self._record(transcript, "normalize", f"len={len(cleaned)}", "ok")
        return cleaned

    def _validate(self, key: str, transcript: List[TranscriptLine]) -> bool:
        if len(key) < 32:
            self._record(transcript, "validate", "length", "fail")
            return False
        if len(key) % 2 != 0:
            self._record(transcript, "validate", "parity", "fail")
            return False
        if not _HEX_RE.match(key):
            self._record(transcript, "validate", "charset", "fail")
            return False
        checksum = sum(int(key[i : i + 2], 16) for i in range(0, len(key), 2)) % 256
        if checksum != 0:
            self._record(transcript, "validate", f"checksum={checksum}", "fail")
            return False
        self._record(transcript, "validate", "checksum=0", "ok")
        return True

    def attest(self, source: str) -> KeyAttestation:
        if source in self._cache:
            cached = self._cache[source]
            transcript = [TranscriptLine(**line.__dict__) for line in cached.transcript]
            return KeyAttestation(key=cached.key, valid=cached.valid, repaired=cached.repaired, transcript=transcript)

        transcript: List[TranscriptLine] = []
        raw = self._load_raw(source, transcript)
        cleaned = self._normalize(raw, transcript)
        valid = self._validate(cleaned, transcript)
        repaired = False
        if not valid:
            repaired_key = cleaned + ("00" if len(cleaned) % 2 else "")
            if repaired_key != cleaned:
                repaired = True
                cleaned = repaired_key
                self._record(transcript, "repair", "padding", "ok")
            else:
                self._record(transcript, "repair", "padding", "skip")
            if self._validate(cleaned, transcript):
                valid = True
                repaired = True
        attestation = KeyAttestation(key=cleaned if valid else None, valid=valid, repaired=repaired, transcript=transcript)
        self._cache[source] = attestation
        return attestation


__all__ = ["FractalKeysmith", "KeyAttestation", "TranscriptLine"]
