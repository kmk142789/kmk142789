"""Seed script for Echo Atlas demo data."""

from __future__ import annotations

from pathlib import Path

from .services import AtlasService


def run(root: Path | None = None) -> None:
    service = AtlasService(root=root)
    service.seed_demo_data()


if __name__ == "__main__":  # pragma: no cover
    run()
