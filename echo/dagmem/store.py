"""Merkle-DAG content addressed storage."""

from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass
from typing import Iterable, List

import hashlib


def cid(data: bytes) -> str:
    return "cid_" + hashlib.sha256(data).hexdigest()


@dataclass(slots=True)
class Node:
    cid: str
    kind: str
    links: List[str]


class FileDisk:
    """Simple file backed disk abstraction used by :class:`DAGStore`."""

    def __init__(self, root: pathlib.Path | str):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, data: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read(self, name: str) -> bytes:
        path = self.root / name
        return path.read_bytes()

    def exists(self, name: str) -> bool:
        return (self.root / name).exists()


class DAGStore:
    def __init__(self, disk: FileDisk | pathlib.Path | str):
        if isinstance(disk, (str, os.PathLike)):
            disk = FileDisk(pathlib.Path(disk))
        self.disk = disk if isinstance(disk, FileDisk) else FileDisk(disk)

    def put_json(self, kind: str, obj: dict, links: Iterable[str] | None = None) -> Node:
        data = json.dumps(obj, sort_keys=True).encode("utf-8")
        link_list = list(links or [])
        content_id = cid(data)
        self.disk.write(content_id + ".json", data)
        self.disk.write(content_id + ".links", "\n".join(link_list).encode("utf-8"))
        return Node(content_id, kind, link_list)

    def get(self, content_id: str) -> dict:
        payload = self.disk.read(content_id + ".json")
        return json.loads(payload.decode("utf-8"))

    def merkle_root(self, heads: Iterable[str]) -> str:
        blob = "|".join(sorted(heads))
        return cid(blob.encode("utf-8"))


__all__ = ["cid", "Node", "FileDisk", "DAGStore"]
