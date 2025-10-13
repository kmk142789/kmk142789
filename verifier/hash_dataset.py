#!/usr/bin/env python3
import argparse
import hashlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="file to hash")
    args = parser.parse_args()

    with open(args.path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()

    out_path = args.path + ".sha256"
    with open(out_path, "w", encoding="utf-8") as out_file:
        out_file.write(digest + "\n")

    print(f"{digest}  {args.path}\n→ {out_path}")


if __name__ == "__main__":
    main()
