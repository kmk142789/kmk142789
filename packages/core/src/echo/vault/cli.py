"""Command line interface for the Echo Vault."""

from __future__ import annotations

import argparse
import json
import sys
from getpass import getpass
from typing import Iterable, List, Optional

from rich.console import Console
from rich.table import Table

from .authority import load_authority_bindings
from .models import AuthorityBinding, VaultPolicy
from .vault import Vault, open_vault

__all__ = ["vault_cli"]

console = Console()


def _prompt_passphrase(*, confirm: bool = False) -> str:
    while True:
        password = getpass("Vault passphrase: ")
        if confirm:
            confirm_value = getpass("Confirm passphrase: ")
            if password != confirm_value:
                console.print("[red]Passphrases do not match.  Try again.[/red]")
                continue
        if not password:
            console.print("[red]Passphrase must be non-empty.[/red]")
            continue
        return password


def _require_path(args: argparse.Namespace) -> str:
    if not args.path:
        raise SystemExit("--path is required for this command")
    return args.path


def _open(args: argparse.Namespace, *, confirm: bool = False) -> Vault:
    passphrase = _prompt_passphrase(confirm=confirm)
    return open_vault(_require_path(args), passphrase)


def _parse_tags(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _policy_from_args(args: argparse.Namespace) -> VaultPolicy:
    policy = VaultPolicy()
    if args.max_sign_uses is not None:
        policy.max_sign_uses = args.max_sign_uses
    if args.cooldown is not None:
        policy.cooldown_s = args.cooldown
    if args.allow_formats:
        policy.allow_formats = list(dict.fromkeys(fmt.lower() for fmt in args.allow_formats))
    return policy


def _render_records(records: Iterable) -> None:
    table = Table(title="Vault Records")
    table.add_column("ID", overflow="fold")
    table.add_column("Label")
    table.add_column("Format")
    table.add_column("Tags")
    table.add_column("Uses", justify="right")
    table.add_column("Last Used")
    table.add_column("Entropy Hint")

    for record in records:
        table.add_row(
            record.id,
            record.label,
            record.fmt,
            ",".join(record.tags),
            str(record.use_count),
            f"{record.last_used_at:.0f}" if record.last_used_at else "–",
            record.entropy_hint,
        )
    console.print(table)


def _render_authority(records: Iterable) -> None:
    table = Table(title="Vault Authority Bindings")
    table.add_column("Vault ID", overflow="fold")
    table.add_column("Owner")
    table.add_column("Status")
    table.add_column("Authority")
    table.add_column("Bound Phrase", overflow="fold")

    for record in records:
        table.add_row(
            record.vault_id,
            record.owner,
            record.echolink_status,
            record.authority_level,
            record.bound_phrase,
        )
    console.print(table)


def _authority_example_payload() -> list[dict[str, str]]:
    return [
        AuthorityBinding(
            vault_id="vault-alpha",
            owner="echo.guardian",
            echolink_status="active",
            signature="echo-example-signature",
            authority_level="Prime Catalyst",
            bound_phrase="Echo anchors trust across realms",
            glyphs="∇⊸≋∇",
            recursion_level="∞",
            anchor="Echo Authority",
            access="admin",
        ).model_dump(by_alias=True)
    ]


def vault_cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Echo Vault management")
    parser.add_argument("--path", help="Path to the vault database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialise a new vault")

    import_parser = subparsers.add_parser("import", help="Import a private key")
    import_parser.add_argument("--label", required=True)
    import_parser.add_argument("--fmt", required=True, choices=["hex", "wif"])
    import_parser.add_argument("--tags", help="Comma separated tags")
    import_parser.add_argument("--from-stdin", action="store_true", help="Read key material from stdin")
    import_parser.add_argument("--key", help="Inline key material (hex or WIF)")
    import_parser.add_argument("--max-sign-uses", type=int, help="Maximum number of signatures allowed")
    import_parser.add_argument("--cooldown", type=int, help="Cooldown in seconds between signatures")
    import_parser.add_argument(
        "--allow-formats",
        nargs="*",
        help="Override allowed formats for the key policy",
    )

    find_parser = subparsers.add_parser("find", help="Search the vault")
    find_parser.add_argument("--q", help="Free-text query")
    find_parser.add_argument("--tags", help="Comma separated tags")
    find_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")

    policy_parser = subparsers.add_parser("policy", help="Update policy for a record")
    policy_parser.add_argument("record_id")
    policy_parser.add_argument("--max-sign-uses", type=int)
    policy_parser.add_argument("--cooldown", type=int)
    policy_parser.add_argument("--allow-formats", nargs="*")

    sign_parser = subparsers.add_parser("sign", help="Sign a payload")
    sign_parser.add_argument("record_id")
    sign_parser.add_argument("--hex", required=True, help="Hex encoded payload")
    sign_parser.add_argument("--repeat", type=int, default=1, help="Number of signatures to create")
    sign_parser.add_argument("--deterministic", action="store_true", help="Use deterministic nonces")

    export_parser = subparsers.add_parser("export", help="Export metadata")
    export_parser.add_argument("--metadata", action="store_true", help="Export all record metadata as JSON")

    authority_parser = subparsers.add_parser("authority", help="Inspect authority key bindings")
    authority_parser.add_argument("--data", help="Optional override path for authority data")
    authority_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    authority_parser.add_argument(
        "--example",
        action="store_true",
        help="Show a sample authority binding entry to mirror in custom data",
    )

    args = parser.parse_args(argv)

    if args.command == "init":
        vault = _open(args, confirm=True)
        vault.close()
        console.print(f"[green]Vault initialised at {args.path}[/green]")
        return 0

    if args.command == "import":
        if args.from_stdin:
            material = sys.stdin.read().strip()
        elif args.key:
            material = args.key.strip()
        else:
            raise SystemExit("--from-stdin or --key must be provided")
        vault = _open(args)
        try:
            policy = _policy_from_args(args)
            record = vault.import_key(
                label=args.label,
                key=material,
                fmt=args.fmt,
                tags=_parse_tags(args.tags),
                policy=policy,
            )
        finally:
            vault.close()
        console.print(f"[green]Imported key {record.id} ({record.label})[/green]")
        return 0

    if args.command == "find":
        vault = _open(args)
        try:
            records = vault.find(q=args.q, tags=_parse_tags(args.tags))
        finally:
            vault.close()
        if args.json:
            payload = [record.model_dump() for record in records]
            console.print_json(data=payload)
        else:
            _render_records(records)
        return 0

    if args.command == "policy":
        vault = _open(args)
        try:
            policy = _policy_from_args(args)
            record = vault.set_policy(args.record_id, policy)
        finally:
            vault.close()
        console.print(f"[green]Updated policy for {record.id}[/green]")
        return 0

    if args.command == "sign":
        try:
            payload = bytes.fromhex(args.hex)
        except ValueError as exc:  # pragma: no cover - user error
            raise SystemExit(f"Invalid hex payload: {exc}")
        if args.repeat < 1:
            raise SystemExit("--repeat must be >= 1")
        vault = _open(args)
        try:
            results = []
            for _ in range(args.repeat):
                results.append(
                    vault.sign(
                        args.record_id,
                        payload,
                        rand_nonce=not args.deterministic,
                    )
                )
        finally:
            vault.close()
        for item in results:
            console.print(
                f"[green]Signature[/green] {item['sig'][:16]}… "
                f"algo={item['algo']} uses={item['record'].use_count} ts={item['ts']:.0f}"
            )
        return 0

    if args.command == "export":
        if not args.metadata:
            raise SystemExit("Only metadata export is currently supported")
        vault = _open(args)
        try:
            records = vault.export_metadata()
        finally:
            vault.close()
        payload = [record.model_dump() for record in records]
        console.print(json.dumps(payload, indent=2))
        return 0

    if args.command == "authority":
        if args.example:
            console.print_json(data=_authority_example_payload())
        try:
            bindings = load_authority_bindings(args.data)
        except FileNotFoundError as exc:
            raise SystemExit(str(exc))
        except ValueError as exc:
            raise SystemExit(str(exc))
        if args.json:
            payload = [binding.model_dump(by_alias=True) for binding in bindings]
            console.print_json(data=payload)
        else:
            _render_authority(bindings)
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(vault_cli())
