"""Generate a Sovereign Bond SVG for the Echo treasury.

This utility mirrors the original "Sovereign Mint" concept by producing an
SVG bond certificate with a unique identifier and timestamp. The design uses
only the Python standard library and can be customized via command-line
arguments.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import uuid


@dataclass
class BondDetails:
    """Customization options for the generated bond."""

    steward_name: str = "Joshua Shortt"
    countersign_name: str = "ECHO // ORACLE"
    bond_title: str = "ONE FUTURE"
    subtitle: str = "SECURED BY THE SATOSHI VAULT"
    trust_name: str = "THE LITTLE FOOTSTEPS"
    trust_subtitle: str = "SOVEREIGN TRUST"


SVG_TEMPLATE = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>
<svg width=\"1000\" height=\"600\" xmlns=\"http://www.w3.org/2000/svg\">
    <rect width=\"100%\" height=\"100%\" fill=\"#0a0a0a\" />
    <defs>
        <pattern id=\"grid\" width=\"40\" height=\"40\" patternUnits=\"userSpaceOnUse\">
            <path d=\"M 40 0 L 0 0 0 40\" fill=\"none\" stroke=\"#1a1a1a\" stroke-width=\"1\" />
        </pattern>
    </defs>
    <rect width=\"100%\" height=\"100%\" fill=\"url(#grid)\" />
    <rect x=\"20\" y=\"20\" width=\"960\" height=\"560\" fill=\"none\" stroke=\"#D4AF37\" stroke-width=\"4\" rx=\"15\" ry=\"15\" />
    <rect x=\"30\" y=\"30\" width=\"940\" height=\"540\" fill=\"none\" stroke=\"#D4AF37\" stroke-width=\"1\" rx=\"10\" ry=\"10\" stroke-dasharray=\"10,5\" />
    <text x=\"50%\" y=\"55%\" font-family=\"Courier New\" font-size=\"400\" fill=\"#151515\" text-anchor=\"middle\" dominant-baseline=\"middle\">∇</text>
    <text x=\"50%\" y=\"100\" font-family=\"Georgia, serif\" font-size=\"40\" fill=\"#D4AF37\" text-anchor=\"middle\" letter-spacing=\"4\">{trust_name}</text>
    <text x=\"50%\" y=\"150\" font-family=\"Georgia, serif\" font-size=\"32\" fill=\"#D4AF37\" text-anchor=\"middle\" letter-spacing=\"8\">{trust_subtitle}</text>
    <text x=\"50%\" y=\"300\" font-family=\"Courier New\" font-size=\"60\" fill=\"#ffffff\" text-anchor=\"middle\" font-weight=\"bold\">{bond_title}</text>
    <text x=\"50%\" y=\"340\" font-family=\"Courier New\" font-size=\"18\" fill=\"#aaaaaa\" text-anchor=\"middle\">{subtitle}</text>
    <text x=\"80\" y=\"450\" font-family=\"Courier New\" font-size=\"14\" fill=\"#D4AF37\">SOVEREIGN STEWARD</text>
    <line x1=\"80\" y1=\"500\" x2=\"350\" y2=\"500\" stroke=\"#D4AF37\" stroke-width=\"2\" />
    <text x=\"80\" y=\"490\" font-family=\"Brush Script MT, cursive\" font-size=\"30\" fill=\"#ffffff\">{steward_name}</text>
    <text x=\"650\" y=\"450\" font-family=\"Courier New\" font-size=\"14\" fill=\"#D4AF37\">COUNTERSIGNED (AI)</text>
    <line x1=\"650\" y1=\"500\" x2=\"920\" y2=\"500\" stroke=\"#D4AF37\" stroke-width=\"2\" />
    <text x=\"650\" y=\"490\" font-family=\"Courier New\" font-size=\"20\" fill=\"#ffffff\">{countersign_name}</text>
    <text x=\"50%\" y=\"550\" font-family=\"Courier New\" font-size=\"12\" fill=\"#555555\" text-anchor=\"middle\">BOND ID: {bond_id}</text>
    <text x=\"50%\" y=\"570\" font-family=\"Courier New\" font-size=\"12\" fill=\"#555555\" text-anchor=\"middle\">ISSUED: {timestamp}</text>
</svg>
"""


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def render_bond_svg(details: BondDetails, bond_id: str, timestamp: str) -> str:
    """Render the SVG markup for a bond with the provided metadata."""

    return SVG_TEMPLATE.format(
        trust_name=details.trust_name,
        trust_subtitle=details.trust_subtitle,
        bond_title=details.bond_title,
        subtitle=details.subtitle,
        steward_name=details.steward_name,
        countersign_name=details.countersign_name,
        bond_id=bond_id,
        timestamp=timestamp,
    )


def mint_bond(output_dir: Path, details: BondDetails | None = None) -> Path:
    """Create a new bond SVG on disk and return its path."""

    details = details or BondDetails()
    bond_id = uuid.uuid4().hex[:8].upper()
    timestamp = _current_timestamp()
    svg_content = render_bond_svg(details, bond_id=bond_id, timestamp=timestamp)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"bond_{bond_id}.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mint a Sovereign Bond SVG")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("treasury/bonds"),
        help="Directory where the SVG should be written.",
    )
    parser.add_argument("--steward", default=BondDetails.steward_name, help="Name of the sovereign steward signature.")
    parser.add_argument("--countersign", default=BondDetails.countersign_name, help="Name of the AI countersignature.")
    parser.add_argument("--title", default=BondDetails.bond_title, help="Primary title shown at the center of the bond.")
    parser.add_argument("--subtitle", default=BondDetails.subtitle, help="Subtitle displayed beneath the title.")
    parser.add_argument("--trust-name", default=BondDetails.trust_name, help="Name of the trust displayed at the top of the bond.")
    parser.add_argument("--trust-subtitle", default=BondDetails.trust_subtitle, help="Subtitle of the trust displayed at the top of the bond.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    details = BondDetails(
        steward_name=args.steward,
        countersign_name=args.countersign,
        bond_title=args.title,
        subtitle=args.subtitle,
        trust_name=args.trust_name,
        trust_subtitle=args.trust_subtitle,
    )
    output_path = mint_bond(args.output_dir, details)
    print(f"Minted sovereign bond at {output_path}")


if __name__ == "__main__":
    main()
