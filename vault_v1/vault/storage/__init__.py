"""Storage backends for Vault v1."""

from .base import StorageBackend
from .local import LocalFileStorage
from .s3 import S3Storage

__all__ = ["StorageBackend", "LocalFileStorage", "S3Storage"]
