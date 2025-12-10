import argparse
import base64
from pathlib import Path


def decode_base64(data: str) -> bytes:
    """Decode a Base64 string with validation and return the raw bytes."""
    return base64.b64decode(data, validate=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Decode a Base64 string and either write the bytes to a file or "
            "print a readable representation to stdout."
        )
    )
    parser.add_argument("data", help="Base64-encoded string to decode")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path to write the decoded bytes. If omitted, the decoded text is printed.",
    )
    args = parser.parse_args()

    decoded = decode_base64(args.data)

    if args.output:
        args.output.write_bytes(decoded)
        print(f"Wrote {len(decoded)} bytes to {args.output}")
        return

    try:
        print(decoded.decode("utf-8"))
    except UnicodeDecodeError:
        print(decoded.hex())


if __name__ == "__main__":
    main()
