"""Data structures describing recovery pointers for Echo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Mapping


@dataclass(slots=True)
class EyePointer:
    """Metadata describing a beacon pointer for Echo recovery."""

    tip: str
    stamp: float
    shares: Mapping[str, str]
    signature: bytes | None = None
    public_key: object | None = None
    metadata: Dict[str, object] = field(default_factory=dict)


ShareFetcher = Callable[[str, str], Awaitable[bytes] | bytes]
