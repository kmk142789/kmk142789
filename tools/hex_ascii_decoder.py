"""Utility for decoding ASCII text from hex-encoded lines.

This helper converts large zero-padded hexadecimal integers into their
printable ASCII representation.  It is especially handy for interpreting
values that have been exported as fixed-width big-endian hex strings where
only the final byte carries meaningful information (for example the list in
which every entry ends with ``2e`` or ``5a``).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

_COMMENT_MARKERS = ("#", ";")


def _normalise_hex(line: str) -> str:
    """Return a hex string with an even number of characters.

    ``bytes.fromhex`` expects an even count of digits.  A small helper keeps
    the command-line interface friendly by padding odd-length inputs with a
    leading zero.  The transformation preserves valid input while making the
    decoder tolerant to user mistakes.
    """

    stripped = line.strip().lower()
    if stripped.startswith("0x"):
        stripped = stripped[2:]

    if len(stripped) % 2:
        stripped = "0" + stripped
    return stripped


def _strip_inline_comment(line: str) -> str:
    """Return ``line`` without inline ``#``, ``;`` or ``//`` comments."""

    earliest = len(line)

    for marker in _COMMENT_MARKERS:
        index = line.find(marker)
        if index != -1 and index < earliest:
            earliest = index

    slash_index = line.find("//")
    if slash_index != -1:
        if slash_index == 0 or line[slash_index - 1].isspace():
            earliest = min(earliest, slash_index)

    return line[:earliest]


def decode_hex_lines(
    lines: Iterable[str],
    *,
    include_nulls: bool = False,
    allow_non_printable: bool = False,
) -> str:
    """Decode hexadecimal strings into ASCII text.

    Parameters
    ----------
    lines:
        The collection of strings to decode.  Each item should contain only
        hexadecimal digits (optionally prefixed with ``0x``).  Inline comments
        introduced by ``#``, ``;`` or ``//`` (after optional whitespace) are
        stripped automatically so clipboard-friendly dumps continue to work.
    include_nulls:
        When ``True`` the decoder keeps ``\x00`` bytes in the output.  The
        default behaviour drops them because they usually represent padding in
        fixed-width exports.
    allow_non_printable:
        When ``False`` (the default) any non-printable ASCII byte triggers a
        ``ValueError``.  Enabling the flag keeps such bytes untouched.
    """

    characters: List[str] = []

    for index, raw_line in enumerate(lines, start=1):
        line = _strip_inline_comment(raw_line).strip()
        if not line:
            continue

        normalised = _normalise_hex(line)

        try:
            data = bytes.fromhex(normalised)
        except ValueError as exc:  # pragma: no cover - defensive path
            raise ValueError(f"Line {index} is not valid hexadecimal: {line}") from exc

        for byte in data:
            if byte == 0 and not include_nulls:
                continue
            if not allow_non_printable and (byte < 32 or byte > 126):
                raise ValueError(
                    f"Line {index} produced a non-printable byte 0x{byte:02x}."
                )
            characters.append(chr(byte))

    return "".join(characters)


def main() -> None:
    """Run the command-line interface."""

    parser = argparse.ArgumentParser(
        description="Decode ASCII characters from lines of hexadecimal integers."
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Optional path to a file.  Reads from stdin when omitted.",
    )
    parser.add_argument(
        "--include-nulls",
        action="store_true",
        help="Keep null (0x00) bytes instead of discarding them.",
    )
    parser.add_argument(
        "--allow-non-printable",
        action="store_true",
        help="Allow bytes outside the printable ASCII range.",
    )

    args = parser.parse_args()

    if args.path:
        lines = args.path.read_text().splitlines()
    else:
        import sys

        lines = sys.stdin.read().splitlines()

    decoded = decode_hex_lines(
        lines,
        include_nulls=args.include_nulls,
        allow_non_printable=args.allow_non_printable,
    )
    print(decoded)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
