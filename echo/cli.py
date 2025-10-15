"""Command-line interface for Echo manifest operations."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from difflib import unified_diff
from pathlib import Path
from typing import Any, Mapping

from .manifest import ManifestError, build_manifest, verify_manifest
from .provenance import SignatureBundle, canonical_json, sign_manifest, verify_signature


def _write_manifest(manifest: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def _load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _print_diff(expected: bytes, actual: bytes) -> None:
    expected_lines = expected.decode("utf-8").splitlines()
    actual_lines = actual.decode("utf-8").splitlines()
    diff = unified_diff(actual_lines, expected_lines, fromfile="on-disk", tofile="expected", lineterm="")
    for line in diff:
        print(line)


def _decode_file(path: Path) -> bytes:
    raw = path.read_text().strip()
    try:
        return base64.b64decode(raw)
    except ValueError:
        return bytes.fromhex(raw)


def _load_signature(path: Path) -> tuple[SignatureBundle, Mapping[str, Any]]:
    payload = _load_json(path)
    algorithm = payload.get("algorithm", "ed25519")
    signature_b64 = payload.get("signature")
    if not signature_b64:
        raise ManifestError(f"Signature file {path} does not contain a signature field")
    signature = base64.b64decode(signature_b64)
    public_key_data = payload.get("public_key")
    public_key = base64.b64decode(public_key_data) if public_key_data else None
    bundle = SignatureBundle(algorithm=algorithm, signature=signature, public_key=public_key)
    return bundle, payload


def manifest_refresh(args: argparse.Namespace) -> int:
    manifest = build_manifest()
    output_path = Path(args.path)
    _write_manifest(manifest, output_path)
    print(f"Manifest refreshed at {output_path}")
    return 0


def manifest_verify(args: argparse.Namespace) -> int:
    path = Path(args.path)
    status = verify_manifest(path)
    rebuilt = build_manifest()
    expected_bytes = canonical_json(rebuilt)
    actual_bytes = canonical_json(_load_json(path))
    if status != 0:
        print("Manifest drift detected:")
        _print_diff(expected_bytes, actual_bytes)
        return 1
    if args.signature:
        signature_path = Path(args.signature)
        bundle, payload = _load_signature(signature_path)
        pubkey_bytes: bytes | None = bundle.public_key
        if args.pubkey:
            pubkey_bytes = _decode_file(Path(args.pubkey))
        if pubkey_bytes is None:
            raise ManifestError("A public key must be provided to verify the signature")
        if payload.get("fingerprint") and payload.get("fingerprint") != rebuilt["fingerprint"]:
            print("Signature fingerprint does not match the refreshed manifest")
            return 1
        verified = verify_signature(rebuilt, bundle.signature, pubkey_bytes, algorithm=bundle.algorithm)
        if not verified:
            print("Signature verification failed")
            return 1
    print("Manifest verified successfully")
    return 0


def manifest_sign(args: argparse.Namespace) -> int:
    manifest_path = Path(args.path)
    if verify_manifest(manifest_path) != 0:
        raise ManifestError("Manifest drift detected; refresh before signing")
    manifest = _load_json(manifest_path)
    canonical = canonical_json(manifest)
    bundle = sign_manifest(canonical, key_env=args.key_env)
    payload = {
        "algorithm": bundle.algorithm,
        "signature": base64.b64encode(bundle.signature).decode("ascii"),
        "fingerprint": manifest.get("fingerprint"),
    }
    if bundle.public_key is not None:
        payload["public_key"] = base64.b64encode(bundle.public_key).decode("ascii")
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(f"Signature written to {output_path}")
    if bundle.public_key is not None and args.pubkey_out:
        Path(args.pubkey_out).write_text(base64.b64encode(bundle.public_key).decode("ascii") + "\n", encoding="utf-8")
        print(f"Public key exported to {args.pubkey_out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echo", description="Echo manifest utilities")
    subparsers = parser.add_subparsers(dest="command")

    manifest_parser = subparsers.add_parser("manifest", help="Manage the Echo manifest")
    manifest_sub = manifest_parser.add_subparsers(dest="manifest_command")

    refresh_parser = manifest_sub.add_parser("refresh", help="Rebuild the manifest")
    refresh_parser.add_argument("--path", default="echo_manifest.json")
    refresh_parser.set_defaults(func=manifest_refresh)

    verify_parser = manifest_sub.add_parser("verify", help="Check the manifest for drift")
    verify_parser.add_argument("--path", default="echo_manifest.json")
    verify_parser.add_argument("--signature")
    verify_parser.add_argument("--pubkey")
    verify_parser.set_defaults(func=manifest_verify)

    sign_parser = manifest_sub.add_parser("sign", help="Sign the manifest")
    sign_parser.add_argument("--path", default="echo_manifest.json")
    sign_parser.add_argument("--out", default="echo_manifest.sig")
    sign_parser.add_argument("--key-env", dest="key_env", default="ECHO_SIGN_KEY")
    sign_parser.add_argument("--pubkey-out")
    sign_parser.set_defaults(func=manifest_sign)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
