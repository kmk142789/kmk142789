from __future__ import annotations

import json
from pathlib import Path

import typer

from .manifest import MANIFEST_PATH, build_manifest, verify_manifest, write_manifest
from .provenance import sign_manifest, verify_signature

app = typer.Typer(add_completion=False, help="Echo CLI")


@app.command("manifest-refresh")
def manifest_refresh(path: str = typer.Option(str(MANIFEST_PATH), "--path", "-p")):
    write_manifest(Path(path))
    typer.echo(f"wrote manifest -> {path}")


@app.command("manifest-verify")
def manifest_verify(path: str = typer.Option(str(MANIFEST_PATH), "--path", "-p")):
    ok = verify_manifest(Path(path))
    if not ok:
        typer.echo("Manifest drift detected. Run `echo manifest-refresh`.", err=True)
        raise typer.Exit(code=1)
    typer.echo("Manifest verified.")


@app.command("manifest-sign")
def manifest_sign(path: str = typer.Option(str(MANIFEST_PATH), "--path", "-p")):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    algo, sig = sign_manifest(manifest)
    out = Path(path).with_suffix(".sig")
    out.write_text(json.dumps({"algo": algo, "signature": sig}, indent=2) + "\n")
    typer.echo(f"signature ({algo}) -> {out}")


@app.command("manifest-verify-signature")
def manifest_verify_signature(
    path: str = typer.Option(str(MANIFEST_PATH), "--path", "-p"),
    sig_path: str = typer.Option(str(MANIFEST_PATH.with_suffix(".sig")), "--sig", "-s"),
):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = json.loads(Path(sig_path).read_text(encoding="utf-8"))
    ok = verify_signature(manifest, meta["signature"], meta["algo"])
    if not ok:
        typer.echo("Signature verification FAILED", err=True)
        raise typer.Exit(code=2)
    typer.echo("Signature OK")


def main():
    app()


if __name__ == "__main__":
    main()
