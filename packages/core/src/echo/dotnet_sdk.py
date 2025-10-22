"""Helpers for working with official .NET SDK download endpoints."""

from __future__ import annotations

import re

_DOTNET_BASE_URL = "https://dotnetcli.blob.core.windows.net/dotnet/Sdk"

_VERSION_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.\-]*$")
_RUNTIME_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*$")
_ARCHIVE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.]*$")


def build_dotnet_sdk_download_url(
    version: str,
    runtime_id: str = "linux-x64",
    archive_format: str = "tar.gz",
) -> str:
    """Return the canonical download URL for the .NET SDK.

    Parameters
    ----------
    version:
        The version string published by Microsoft, for example ``"8.0.400"`` or
        ``"9.0.0-preview.2.24157.9"``.  The helper performs light validation to
        guard against path traversal or shell injection by ensuring only
        alphanumeric characters, dots, and hyphens are present.
    runtime_id:
        The runtime identifier segment that appears at the end of the
        distribution file name.  ``"linux-x64"`` is the default matching the
        user-provided URL format.
    archive_format:
        The archive extension used by the distribution.  ``"tar.gz"`` is used
        for Linux builds, while Windows builds typically use ``"zip"``.  The
        argument may optionally start with a leading dot, which will be ignored.

    Returns
    -------
    str
        The fully-qualified HTTPS URL pointing at the corresponding SDK
        artifact hosted on Microsoft's blob storage endpoint.

    Raises
    ------
    ValueError
        If any component fails validation.
    """

    if not isinstance(version, str) or not version:
        raise ValueError("version must be a non-empty string")
    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid .NET SDK version: {version!r}")

    if not isinstance(runtime_id, str) or not runtime_id:
        raise ValueError("runtime_id must be a non-empty string")
    if not _RUNTIME_ID_PATTERN.fullmatch(runtime_id):
        raise ValueError(f"invalid runtime identifier: {runtime_id!r}")

    if not isinstance(archive_format, str) or not archive_format:
        raise ValueError("archive_format must be a non-empty string")
    if archive_format.startswith(".."):
        raise ValueError(f"invalid archive format: {archive_format!r}")
    normalized_archive = archive_format.lstrip(".")
    if normalized_archive.count(".") > 1:
        raise ValueError(f"invalid archive format: {archive_format!r}")
    if not _ARCHIVE_PATTERN.fullmatch(normalized_archive):
        raise ValueError(f"invalid archive format: {archive_format!r}")

    return (
        f"{_DOTNET_BASE_URL}/{version}/"
        f"dotnet-sdk-{version}-{runtime_id}.{normalized_archive}"
    )


__all__ = ["build_dotnet_sdk_download_url"]
