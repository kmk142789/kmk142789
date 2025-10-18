#!/usr/bin/env python3
"""Utility helpers for inspecting chained base64 wallet message signatures.

This module provides a small command line interface that can be used to
sanity-check a blob composed of multiple base64-encoded signatures that have
been appended together by repeatedly signing previous outputs, as described in
wallet message workflows.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from dataclasses import dataclass, field
from typing import Iterable, Sequence


class SignatureFormatError(ValueError):
    """Raised when an entry in the blob is not a plausible base64 signature."""


@dataclass
class SignatureChain:
    """Container for an ordered set of base64 signature fragments."""

    entries: Sequence[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate all entries as strict base64 strings.

        Raises
        ------
        SignatureFormatError
            If an entry cannot be decoded as base64 or falls outside the
            expected size range (88-92 characters for legacy message
            signatures, although the bounds can be slightly wider for modern
            wallet implementations).
        """

        for idx, token in enumerate(self.entries):
            stripped = token.strip()
            if not stripped:
                raise SignatureFormatError(
                    f"Entry {idx + 1} is empty after trimming whitespace."
                )

            if len(stripped) < 80 or len(stripped) > 128:
                raise SignatureFormatError(
                    f"Entry {idx + 1} has an unexpected length of "
                    f"{len(stripped)} characters."
                )

            try:
                base64.b64decode(stripped, validate=True)
            except Exception as exc:  # noqa: BLE001
                raise SignatureFormatError(
                    f"Entry {idx + 1} is not valid base64: {exc}"
                ) from exc

    @property
    def blob(self) -> str:
        """Return the concatenated blob that a wallet would sign next."""

        return "".join(self.entries)

    def describe(self) -> dict:
        """Return a JSON-serialisable description of the chain."""

        lengths = [len(entry.strip()) for entry in self.entries]
        return {
            "entry_count": len(self.entries),
            "length_min": min(lengths) if lengths else 0,
            "length_max": max(lengths) if lengths else 0,
            "lengths": lengths,
            "blob_char_count": len(self.blob),
        }

    @classmethod
    def from_blob(cls, blob: str) -> "SignatureChain":
        entries = [chunk for chunk in blob.split() if chunk]
        return cls(entries=entries)


def _read_blob(args: argparse.Namespace) -> str:
    if args.from_file:
        return args.from_file.read()
    if args.blob:
        return args.blob
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide --blob, --from-file, or pipe data via stdin.")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a blob composed of chained base64 wallet message "
            "signatures."
        )
    )
    parser.add_argument(
        "blob",
        nargs="?",
        help="Space or newline separated base64 signatures to inspect.",
    )
    parser.add_argument(
        "--from-file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Read the signature blob from a file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON for scripting.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    blob = _read_blob(args)
    chain = SignatureChain.from_blob(blob)

    try:
        chain.validate()
    except SignatureFormatError as exc:
        parser.error(str(exc))

    description = chain.describe()
    if args.json:
        json.dump(description, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("Signature entries:", description["entry_count"])
        if description["entry_count"]:
            print(
                "Length range:",
                f"{description['length_min']} - {description['length_max']} characters",
            )
            print("Individual lengths:", ", ".join(map(str, description["lengths"])))
            print("Combined blob characters:", description["blob_char_count"])
            print("Next message to sign (concatenated blob):")
            print(chain.blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
