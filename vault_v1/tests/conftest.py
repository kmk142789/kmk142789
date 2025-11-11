from __future__ import annotations

import importlib
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def configure_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "vault.db"
    storage_path = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("VAULT_LOCAL_PATH", str(storage_path))
    monkeypatch.setenv("VAULT_BACKEND", "local")
    monkeypatch.delenv("VAULT_SIGNING_KEY", raising=False)

    from vault import config, models

    importlib.reload(config)
    config.get_settings.cache_clear()
    importlib.reload(models)
    models.reset_engine()

    from vault.models import Base, get_engine

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    config.get_settings.cache_clear()
    models.reset_engine()
