"""Adapter registry for Dominion plan execution."""

from .fs import FileSystemAdapter
from .git import GitAdapter
from .http import HTTPAdapter
from .archive import ArchiveAdapter

__all__ = [
    "FileSystemAdapter",
    "GitAdapter",
    "HTTPAdapter",
    "ArchiveAdapter",
]
