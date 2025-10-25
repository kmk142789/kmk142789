"""Utilities for resolving and downloading Swarm (``bzz``) resources.

The repository occasionally references Swarm URIs (e.g. ``bzzr://`` hashes)
from governance artefacts.  These helpers provide a small, dependency-free
utility to normalise the URIs into HTTP gateway URLs and optionally download
artifacts.  The goal is to make it easy to inspect provenance payloads without
manually crafting gateway URLs each time.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import os
from pathlib import Path
from typing import Callable, Sequence
import sys
import urllib.parse
import urllib.request

DEFAULT_GATEWAY = "https://swarm-gateways.net"
SUPPORTED_SCHEMES = {"bzz", "bzzr", "bzz-raw"}


@dataclass(frozen=True)
class SwarmURI:
    """Parsed Swarm URI (``bzz://`` / ``bzzr://``)."""

    scheme: str
    reference: str
    path: str = ""

    @property
    def normalized_scheme(self) -> str:
        """Return the canonical scheme name (``bzz`` or ``bzz-raw``)."""

        if self.scheme in {"bzzr", "bzz-raw"}:
            return "bzz-raw"
        return "bzz"

    def to_gateway_url(self, base_gateway: str) -> str:
        """Build an HTTP gateway URL for this Swarm URI.

        Parameters
        ----------
        base_gateway:
            Base HTTP gateway URL (e.g. ``https://swarm-gateways.net``).
        """

        base = base_gateway.rstrip("/") or DEFAULT_GATEWAY
        resource_prefix = f"{self.normalized_scheme}:/"
        suffix = f"/{self.path}" if self.path else "/"
        return f"{base}/{resource_prefix}{self.reference}{suffix}"


def parse_swarm_uri(uri: str) -> SwarmURI:
    """Parse ``bzz``/``bzzr`` URIs into a :class:`SwarmURI`.

    Supports the two common syntaxes (``bzzr://hash`` and ``bzzr:hash``).
    Raises :class:`ValueError` for unsupported schemes or malformed values.
    """

    parsed = urllib.parse.urlparse(uri)
    scheme = parsed.scheme.lower()
    if scheme not in SUPPORTED_SCHEMES:
        raise ValueError(f"Unsupported Swarm scheme: {parsed.scheme!r}")

    if parsed.query or parsed.fragment or parsed.params:
        raise ValueError("Swarm URIs must not include params, query, or fragment")

    if parsed.netloc:
        reference = parsed.netloc
        path = parsed.path.lstrip("/")
    else:
        path_parts = parsed.path.lstrip("/").split("/", 1)
        reference = path_parts[0]
        path = path_parts[1] if len(path_parts) == 2 else ""

    if not reference:
        raise ValueError("Swarm URI is missing the content hash")

    return SwarmURI(scheme=scheme, reference=reference, path=path)


def resolve_swarm_uri(uri: str, *, gateway: str | None = None) -> str:
    """Convert a Swarm URI into a concrete HTTP gateway URL."""

    swarm_uri = parse_swarm_uri(uri)
    base = gateway or os.getenv("SWARM_HTTP_GATEWAY") or DEFAULT_GATEWAY
    return swarm_uri.to_gateway_url(base)


def fetch_swarm_uri(
    uri: str,
    *,
    gateway: str | None = None,
    opener: Callable[[str], object] | None = None,
) -> bytes:
    """Fetch the payload referenced by the Swarm URI.

    ``opener`` allows dependency injection for tests.  It must return an object
    that exposes ``read()`` and supports the context manager protocol.
    """

    url = resolve_swarm_uri(uri, gateway=gateway)
    open_fn: Callable[[str], object]
    open_fn = opener or urllib.request.urlopen
    with open_fn(url) as response:  # type: ignore[attr-defined]
        data = response.read()  # type: ignore[attr-defined]
    return data


def _write_payload(data: bytes, output: Path | None) -> None:
    if output is None:
        sys.stdout.buffer.write(data)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Swarm (bzz) resources")
    parser.add_argument("uri", help="Swarm URI (bzz:// or bzzr://)")
    parser.add_argument(
        "--gateway",
        help="HTTP gateway base URL (defaults to $SWARM_HTTP_GATEWAY or %s)" % DEFAULT_GATEWAY,
    )
    parser.add_argument("--output", help="Write payload to this file path")
    parser.add_argument(
        "--print-url",
        action="store_true",
        help="Print the resolved HTTP URL before downloading",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the URL but skip downloading the payload",
    )

    args = parser.parse_args(argv)
    gateway = args.gateway or os.getenv("SWARM_HTTP_GATEWAY")
    url = resolve_swarm_uri(args.uri, gateway=gateway)

    if args.print_url:
        print(url)

    if args.dry_run:
        return 0

    data = fetch_swarm_uri(args.uri, gateway=gateway)
    output_path = Path(args.output) if args.output else None
    _write_payload(data, output_path)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
