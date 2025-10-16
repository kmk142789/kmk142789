from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .manifest import MANIFEST_PATH, verify_manifest, write_manifest
from .provenance import sign_manifest, verify_signature


def _manifest_refresh(path: Path) -> int:
    write_manifest(path)
    print(f"wrote manifest -> {path}")
    return 0


def _manifest_verify(path: Path) -> int:
    if not verify_manifest(path):
        print("Manifest drift detected. Run `echo manifest-refresh`.", file=sys.stderr)
        return 1
    print("Manifest verified.")
    return 0


def _manifest_sign(path: Path) -> int:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    algo, sig = sign_manifest(manifest)
    out = path.with_suffix(".sig")
    out.write_text(json.dumps({"algo": algo, "signature": sig}, indent=2) + "\n")
    print(f"signature ({algo}) -> {out}")
    return 0


def _manifest_verify_signature(path: Path, sig_path: Path) -> int:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    meta = json.loads(sig_path.read_text(encoding="utf-8"))
    if not verify_signature(manifest, meta["signature"], meta["algo"]):
        print("Signature verification FAILED", file=sys.stderr)
        return 2
    print("Signature OK")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo CLI")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    refresh = subparsers.add_parser("manifest-refresh", help="Rebuild the manifest")
    refresh.add_argument("--path", "-p", type=Path, default=MANIFEST_PATH, help="Path to manifest")

    verify = subparsers.add_parser("manifest-verify", help="Ensure manifest matches repo state")
    verify.add_argument("--path", "-p", type=Path, default=MANIFEST_PATH, help="Path to manifest")

    sign = subparsers.add_parser("manifest-sign", help="Sign a manifest")
    sign.add_argument("--path", "-p", type=Path, default=MANIFEST_PATH, help="Path to manifest")

    verify_sig = subparsers.add_parser("manifest-verify-signature", help="Verify a manifest signature")
    verify_sig.add_argument("--path", "-p", type=Path, default=MANIFEST_PATH, help="Path to manifest")
    verify_sig.add_argument(
        "--sig",
        "-s",
        dest="sig_path",
        type=Path,
        default=MANIFEST_PATH.with_suffix(".sig"),
        help="Path to signature metadata",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "manifest-refresh":
        return _manifest_refresh(args.path)
    if args.command == "manifest-verify":
        return _manifest_verify(args.path)
    if args.command == "manifest-sign":
        return _manifest_sign(args.path)
    if args.command == "manifest-verify-signature":
        return _manifest_verify_signature(args.path, args.sig_path)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
