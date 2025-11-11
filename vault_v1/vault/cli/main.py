from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import click

from ..config import get_settings
from ..hashing import compute_merkle_root
from ..services.ingest import ingest_stream
from ..services.retrieve import retrieve_file
from .keygen import generate_key


@click.group()
def cli() -> None:
    """Vault v1 command line interface."""


@cli.command()
@click.option("--out", "out_path", default="keys/signing.json", type=click.Path(path_type=Path))
def keygen(out_path: Path) -> None:
    """Generate an ES256 signing key."""
    path = generate_key(out_path)
    click.echo(f"Key written to {path}")


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--chunk-size", type=int, default=None, help="Chunk size in bytes")
@click.option("--sign", is_flag=True, help="Sign ingest receipt")
def ingest(path: Path, chunk_size: int | None, sign: bool) -> None:
    """Ingest a file into the vault."""
    settings = get_settings()
    chosen_chunk_size = chunk_size or settings.default_chunk_size
    mime, _ = mimetypes.guess_type(str(path))
    with path.open("rb") as stream:
        result = ingest_stream(
            stream=stream,
            filename=path.name,
            mime_type=mime,
            chunk_size=chosen_chunk_size,
            sign_receipt=sign,
            uploader="cli",
        )
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.argument("cid")
@click.option("--out", "out_path", type=click.Path(path_type=Path))
@click.option("--sign", is_flag=True, help="Request signed receipt")
def fetch(cid: str, out_path: Path | None, sign: bool) -> None:
    """Fetch a file from the vault."""
    result = retrieve_file(cid, sign_receipt=sign)
    target = out_path or Path(cid)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f:
        for chunk in result["chunks"]:
            f.write(chunk)
    payload = {
        "cid": cid,
        "path": str(target),
        "bytes": result["metadata"]["total_size"],
    }
    if sign:
        payload["receipt"] = result["receipt"]
    click.echo(json.dumps(payload, indent=2))


@cli.command()
@click.argument("cid")
@click.option("--sign", is_flag=True, help="Request signed receipt")
def proof(cid: str, sign: bool) -> None:
    """Print the Merkle proof for a file."""
    result = retrieve_file(cid, sign_receipt=sign)
    proof_payload = {
        "cid": cid,
        "merkle_root": result["metadata"]["merkle_root"],
        "chunk_hashes": result["chunk_hashes"],
        "verified": compute_merkle_root(result["chunk_hashes"]) == result["metadata"]["merkle_root"],
    }
    if sign:
        proof_payload["receipt"] = result["receipt"]
    click.echo(json.dumps(proof_payload, indent=2))


if __name__ == "__main__":  # pragma: no cover
    cli()
