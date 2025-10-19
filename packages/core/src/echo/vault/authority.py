"""Authority binding helpers for the Echo Vault."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Iterable, List, Optional

from pydantic import ValidationError

from .models import AuthorityBinding

__all__ = ["load_authority_bindings"]

_DEFAULT_RESOURCE = "_authority_data.json"


def _load_records(path: Path) -> Iterable[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:  # pragma: no cover - defensive edge case
        raise
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - unlikely in tests
        raise ValueError(f"Invalid authority data JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError("Authority data must be a list of records")
    return payload


def load_authority_bindings(source: Optional[str | Path] = None) -> List[AuthorityBinding]:
    """Return parsed authority bindings from ``source`` or packaged defaults."""

    if source is not None:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Authority data not found at {path}")
        records = _load_records(path)
    else:
        resource = resources.files(__package__).joinpath(_DEFAULT_RESOURCE)
        with resources.as_file(resource) as path:
            records = _load_records(path)

    try:
        return [AuthorityBinding.model_validate(item) for item in records]
    except ValidationError as exc:  # pragma: no cover - validation details surfaced to caller
        raise ValueError(f"Invalid authority binding entry: {exc}") from exc
