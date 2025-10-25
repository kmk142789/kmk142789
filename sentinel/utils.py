from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def isoformat(dt: datetime | None = None) -> str:
    value = dt or utc_now()
    return value.strftime(ISO_FORMAT)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, sort_keys=True)
        fp.write("\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_mode(path: Path) -> str:
    try:
        st_mode = path.stat().st_mode
    except FileNotFoundError:
        return "missing"
    if stat.S_ISDIR(st_mode):
        return "directory"
    if stat.S_ISLNK(st_mode):
        return "symlink"
    return "file"


def relpath(path: Path, start: Path | None = None) -> str:
    start = start or Path.cwd()
    try:
        return str(path.relative_to(start))
    except ValueError:
        return str(path)


def to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def from_iterable(value: Iterable[Any]) -> list[Any]:
    return [item for item in value]


def load_registry(path: Path | None) -> Mapping[str, Any]:
    if path and path.exists():
        return read_json(path)
    default = Path("build/dominion/registry.json")
    if default.exists():
        return read_json(default)
    fallback = Path("registry.json")
    if fallback.exists():
        return read_json(fallback)
    return {"fragments": []}


@dataclass
class Finding:
    probe: str
    subject: str
    status: str
    message: str
    data: Mapping[str, Any]

    def sarif_level(self) -> str:
        return {
            "ok": "note",
            "info": "note",
            "warning": "warning",
            "error": "error",
        }.get(self.status, "note")


def multiline(text: str) -> str:
    return textwrap.dedent(text).strip()


def coerce_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def encode_payload(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    return to_base64(body)


def digest_payload(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def safe_glob(directory: Path, pattern: str) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(pattern))


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def merge_dicts(*items: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in items:
        merged.update(item)
    return merged


def environment_flag(name: str) -> bool:
    return coerce_bool(os.environ.get(name))


def dataclass_to_dict(instance: Any) -> dict[str, Any]:
    if dataclass_isinstance(instance):
        return asdict(instance)
    raise TypeError(f"{instance!r} is not a dataclass instance")


def dataclass_isinstance(instance: Any) -> bool:
    return hasattr(instance, "__dataclass_fields__")

