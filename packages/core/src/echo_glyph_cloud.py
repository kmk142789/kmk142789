"""Digital Echo cloud sustained by glyph anchors rather than physical servers.

The goal of the :mod:`echo_glyph_cloud` module is to model a "cloud" that only
exists wherever Echo glyphs are present.  Instead of standing up networked
infrastructure, we treat each glyph as an anchor that can hold imprints of data
and project those imprints across a constellation of virtual nodes.  The
resulting structure is fully digital and portable; bring the glyphs with you and
the cloud appears.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence

__all__ = ["GlyphImprint", "GlyphAnchor", "DataGlyph", "EchoGlyphCloud"]


@dataclass(slots=True)
class GlyphImprint:
    """A single piece of data imprinted onto a glyph anchor."""

    payload: str
    tags: tuple[str, ...] = ()
    virtual_nodes: tuple[str, ...] = ()
    timestamp: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, object]:
        return {
            "payload": self.payload,
            "tags": list(self.tags),
            "virtual_nodes": list(self.virtual_nodes),
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class GlyphAnchor:
    """Anchor that binds glyph symbols to their imprinted data."""

    glyph: str
    metadata: MutableMapping[str, object] = field(default_factory=dict)
    imprints: list[GlyphImprint] = field(default_factory=list)

    def bind_metadata(self, updates: Mapping[str, object]) -> None:
        """Merge new metadata into the anchor without overwriting existing keys."""

        for key, value in updates.items():
            if key not in self.metadata:
                self.metadata[key] = value

    @property
    def imprint_count(self) -> int:
        return len(self.imprints)

    def to_dict(self) -> Dict[str, object]:
        return {
            "glyph": self.glyph,
            "metadata": dict(self.metadata),
            "imprint_count": self.imprint_count,
            "imprints": [imprint.to_dict() for imprint in self.imprints],
        }


@dataclass(slots=True, frozen=True)
class DataGlyph:
    """Summary artifact describing the data bound to a glyph anchor."""

    glyph: str
    fingerprint: str
    imprint_count: int
    tags: tuple[str, ...]
    metadata: Mapping[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "glyph": self.glyph,
            "fingerprint": self.fingerprint,
            "imprint_count": self.imprint_count,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


class EchoGlyphCloud:
    """A purely digital Echo cloud anchored by glyphs.

    Each glyph that is registered with the cloud becomes a deterministic anchor
    point.  When data is stored against the anchor we derive a network of virtual
    nodes using the glyph symbol.  The nodes are represented by opaque strings
    rather than server identifiers, reinforcing the idea that the cloud exists
    wherever the glyphs are summoned.
    """

    def __init__(self, *, anchor_prefix: str = "∇⊸≋∇", nodes_per_imprint: int = 3):
        if nodes_per_imprint <= 0:
            raise ValueError("nodes_per_imprint must be positive")
        self.anchor_prefix = anchor_prefix
        self.nodes_per_imprint = nodes_per_imprint
        self._anchors: Dict[str, GlyphAnchor] = {}

    @property
    def anchors(self) -> Sequence[GlyphAnchor]:
        return tuple(self._anchors.values())

    def register_anchor(self, glyph: str, *, metadata: Mapping[str, object] | None = None) -> GlyphAnchor:
        if not glyph:
            raise ValueError("glyph must be a non-empty string")
        anchor = self._anchors.get(glyph)
        if anchor is None:
            anchor = GlyphAnchor(glyph=glyph)
            self._anchors[glyph] = anchor
        if metadata:
            anchor.bind_metadata(metadata)
        return anchor

    def imprint(
        self,
        glyph: str,
        payload: str,
        *,
        tags: Iterable[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> GlyphImprint:
        """Imprint ``payload`` onto ``glyph`` and return the resulting record."""

        anchor = self.register_anchor(glyph, metadata=metadata)
        unique_tags = self._normalise_tags(tags)
        virtual_nodes = self._derive_virtual_nodes(glyph, self.nodes_per_imprint + len(unique_tags))
        imprint = GlyphImprint(payload=payload, tags=unique_tags, virtual_nodes=virtual_nodes)
        anchor.imprints.append(imprint)
        return imprint

    def manifest(self) -> Dict[str, object]:
        """Return a serialisable representation of the entire cloud."""

        return {
            "anchor_prefix": self.anchor_prefix,
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "data_glyphs": [self.forge_data_glyph(anchor.glyph).to_dict() for anchor in self.anchors],
        }

    def describe_anchor(self, glyph: str) -> str:
        """Return a human-readable summary for a glyph anchor."""

        anchor = self._anchors.get(glyph)
        if anchor is None:
            raise KeyError(f"No anchor registered for glyph {glyph!r}")
        lines = [f"Glyph {anchor.glyph} :: {anchor.imprint_count} imprints"]
        if anchor.metadata:
            metadata_pairs = ", ".join(f"{key}={value}" for key, value in sorted(anchor.metadata.items()))
            lines.append(f"Metadata: {metadata_pairs}")
        for imprint in anchor.imprints:
            tag_section = f" tags={','.join(imprint.tags)}" if imprint.tags else ""
            nodes_preview = ", ".join(imprint.virtual_nodes[:3])
            lines.append(f"- {imprint.payload[:48]}{tag_section} @ {nodes_preview}")
        return "\n".join(lines)

    def forge_data_glyph(self, glyph: str) -> DataGlyph:
        """Derive a deterministic summary glyph for ``glyph``."""

        anchor = self._anchors.get(glyph)
        if anchor is None:
            raise KeyError(f"No anchor registered for glyph {glyph!r}")

        digest = hashlib.sha256()
        digest.update(f"{self.anchor_prefix}:{glyph}".encode("utf-8"))

        metadata_snapshot = dict(anchor.metadata)
        for key, value in sorted(metadata_snapshot.items()):
            digest.update(f"{key}={value}".encode("utf-8"))

        aggregate_tags: list[str] = []
        seen_tags: set[str] = set()
        for imprint in anchor.imprints:
            digest.update(imprint.payload.encode("utf-8"))
            digest.update("::".join(imprint.tags).encode("utf-8"))
            digest.update("|".join(imprint.virtual_nodes).encode("utf-8"))
            digest.update(f"{imprint.timestamp:.6f}".encode("utf-8"))
            for tag in imprint.tags:
                if tag and tag not in seen_tags:
                    aggregate_tags.append(tag)
                    seen_tags.add(tag)

        fingerprint = digest.hexdigest()
        return DataGlyph(
            glyph=glyph,
            fingerprint=fingerprint,
            imprint_count=anchor.imprint_count,
            tags=tuple(aggregate_tags),
            metadata=metadata_snapshot,
        )

    def data_glyph_ledger(self, *, tags: Iterable[str] | None = None) -> list[Dict[str, object]]:
        """Return data glyphs, optionally filtered by tag membership."""

        tag_filter = tuple(dict.fromkeys(tag for tag in (tags or ()) if tag))
        if tag_filter:
            filter_set = set(tag_filter)
        else:
            filter_set = set()

        ledger: list[Dict[str, object]] = []
        for anchor in self.anchors:
            data_glyph = self.forge_data_glyph(anchor.glyph)
            if filter_set and not any(tag in filter_set for tag in data_glyph.tags):
                continue
            ledger.append(data_glyph.to_dict())
        return ledger

    def _derive_virtual_nodes(self, glyph: str, count: int) -> tuple[str, ...]:
        digest = hashlib.sha256(f"{self.anchor_prefix}:{glyph}".encode("utf-8")).hexdigest()
        segments = [digest[i : i + 8] for i in range(0, count * 8, 8)]
        return tuple(f"{glyph}::{segment}" for segment in segments)

    @staticmethod
    def _normalise_tags(tags: Iterable[str] | None) -> tuple[str, ...]:
        if not tags:
            return ()
        return tuple(dict.fromkeys(tag for tag in tags if tag))

