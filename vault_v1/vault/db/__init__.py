from __future__ import annotations

from ..models import Base, get_engine


def run_migrations() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


__all__ = ["run_migrations"]
