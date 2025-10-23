"""Universal script decoding CLI with Bitcoin compatibility helpers."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .script_decoder import (
    ScriptDecodingError,
    ScriptDecodingResult,
    decode_script,
    registry,
)


def pkscript_to_address(lines: Iterable[str], network: str = "mainnet") -> str:
    """Convert a textual Bitcoin script to an address using the shared decoder."""

    result = decode_script("bitcoin", list(lines), network=network)
    if not result.addresses:
        raise ScriptDecodingError("decoder did not return an address")
    return result.addresses[0]


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        help="path to the script description; omit to read from stdin",
    )
    parser.add_argument(
        "--chain",
        default="bitcoin",
        choices=tuple(registry.chains()),
        help="target chain for decoding",
    )
    parser.add_argument(
        "--network",
        default="mainnet",
        help="Bitcoin network identifier (only used for bitcoin chain)",
    )
    parser.add_argument(
        "--mode",
        help="optional decoder mode override (e.g. calldata for Ethereum)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit full JSON decoding results instead of a compact summary",
    )
    return parser


def _read_script(path: str | None) -> list[str]:
    if path:
        with open(path, "r", encoding="utf8") as handle:
            return handle.readlines()
    import sys

    return sys.stdin.readlines()


def _result_to_output(result: ScriptDecodingResult, *, json_mode: bool) -> str:
    if json_mode or result.chain != "bitcoin":
        return json.dumps(result.to_dict(), indent=2, sort_keys=True)

    if not result.addresses:
        raise ScriptDecodingError("no address decoded for Bitcoin script")
    return result.addresses[0]


def main() -> int:
    parser = _build_cli()
    args = parser.parse_args()

    lines = _read_script(args.path)
    kwargs = {}
    if args.mode:
        kwargs["mode"] = args.mode
    if args.chain == "bitcoin":
        kwargs["network"] = args.network

    result = decode_script(args.chain, lines, **kwargs)
    output = _result_to_output(result, json_mode=args.json)
    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())

