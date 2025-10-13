"""Peer definitions for EchoNet federation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Peer:
    """Representation of a remote Echo node in the federation."""

    id: str
    url: str
    pubkey: str
