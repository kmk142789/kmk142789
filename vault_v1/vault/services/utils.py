from __future__ import annotations

from typing import Optional

from ..config import get_settings
from ..storage.local import LocalFileStorage
from ..storage.s3 import S3Storage
from ..storage.base import StorageBackend


_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    settings = get_settings()
    if settings.vault_backend == "local":
        _storage_instance = LocalFileStorage(settings.vault_local_path)
    else:
        if not settings.aws_bucket:  # pragma: no cover - configuration guard
            raise ValueError("VAULT_S3_BUCKET must be set for s3 backend")
        client_kwargs = {}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            client_kwargs.update(
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        if settings.aws_region:
            client_kwargs["region_name"] = settings.aws_region
        _storage_instance = S3Storage(bucket=settings.aws_bucket, **client_kwargs)
    return _storage_instance


__all__ = ["get_storage"]
