"""Routing layer for the vault HTTP API."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import Dict, Mapping, Tuple

from ..models import APIError, IntegrityReport
from ..services.metadata import ChangeJournal, MetadataIndex
from ..services.storage import ContentAddressableStore


class VaultRouter:
    """Maps HTTP verbs and paths to handlers."""

    def __init__(self, store: ContentAddressableStore, index: MetadataIndex, journal: ChangeJournal) -> None:
        self.store = store
        self.index = index
        self.journal = journal

    def handle_post_items(self, body: bytes) -> Tuple[int, Dict[str, str]]:
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("invalid JSON payload")
        content = payload.get("content")
        metadata = payload.get("metadata", {})
        if content is None:
            raise ValueError("missing 'content' field")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        stored = self.store.store(content.encode("utf-8"), metadata)
        self.index.update(stored)
        self.journal.append("store", stored.address, {"metadata": metadata})
        return HTTPStatus.CREATED, stored.to_dict()

    def handle_get_items(self, query: Mapping[str, str]) -> Tuple[int, Dict[str, object]]:
        if not query:
            items = [item.to_dict() for item in self.store.iter_items()]
            return HTTPStatus.OK, {"items": items}
        addresses = self.index.query(query)
        hits = [self.store.fetch(address).to_dict() for address in addresses if self.store.fetch(address)]
        return HTTPStatus.OK, {"items": hits}

    def handle_get_history(self) -> Tuple[int, Dict[str, object]]:
        records = [record.to_dict() for record in self.journal.iter()]
        return HTTPStatus.OK, {"history": records}

    def handle_get_integrity(self) -> Tuple[int, Dict[str, object]]:
        report: IntegrityReport = self.store.verify_integrity()
        return HTTPStatus.OK, report.to_dict()

    def error(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> Tuple[int, Dict[str, object]]:
        return status, APIError(message=message).to_dict()
