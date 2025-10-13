# Thin wrapper: adapt to your existing generator (reuse your echo_glyphs functions)
import hashlib
from pathlib import Path
from typing import Dict


def make_glyphs(
    data: str | None = None,
    file: str | None = None,
    salt: str = "∇⊸≋∇",
    out_dir: str = "glyphs_out",
    size: int = 256,
    tile: int = 6,
) -> Dict:
    """Generate glyph SVGs and an aggregate sheet.

    Parameters mirror the legacy ``echo_glyphs`` entry points so the CLI
    remains a thin compatibility layer for the prior generator.
    """

    # import your previous generator functions dynamically to avoid duplication
    from verifier.echo_glyphs import (
        bytes_from_args,
        glyph_svg,
        make_sheet,
        write_file,
    )  # adjust path if needed

    payload = bytes_from_args(data or "", file, salt)
    seed = int.from_bytes(hashlib.sha256(salt.encode()).digest()[:8], "big")
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    written = []
    for i, b in enumerate(payload):
        p = outp / f"glyph_{i:03d}.svg"
        write_file(str(p), glyph_svg(b, seed, size=size))
        written.append(str(p))
    sheet = outp / "sheet.svg"
    make_sheet(written, tile=tile, size=size, out=str(sheet))
    checksum = hashlib.sha256("".join(written).encode()).hexdigest()
    return {"count": len(written), "sheet": str(sheet), "checksum": checksum}
