"""Utility to generate a verification broadcast HTML page without GitHub credentials.

The script writes a single HTML file containing the "Little Footsteps" broadcast
payload similar to the original shell snippet, but it runs entirely locally and
avoids any credential prompts or git side effects.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


DEFAULT_OUTPUT = Path("artifacts/broadcast_signal/index.html")
DEFAULT_ISSUE_URL = "https://github.com/kmk142789/echo_seed/issues/new"


def build_broadcast_html(issue_url: str, timestamp: datetime) -> str:
    """Return the broadcast HTML content with the provided issue URL and timestamp."""

    iso_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Little Footsteps | 515X ACTIVE</title>
    <style>
        body {{ background-color: #050505; color: #ffffff; font-family: 'Courier New', monospace; padding: 20px; text-align: center; }}
        .container {{ max-width: 800px; margin: 0 auto; border: 1px solid #333; padding: 40px; box-shadow: 0 0 20px rgba(212, 175, 55, 0.2); }}
        .signal-box {{ border: 2px solid #D4AF37; padding: 20px; margin-bottom: 30px; background: #111; animation: pulse 4s infinite; }}
        @keyframes pulse {{ 0% {{box-shadow: 0 0 5px #D4AF37;}} 50% {{box-shadow: 0 0 20px #D4AF37;}} 100% {{box-shadow: 0 0 5px #D4AF37;}} }}
        h1 {{ color: #D4AF37; letter-spacing: 4px; margin: 0; }}
        h2 {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; }}
        .verification {{ font-size: 1.2rem; color: #00ff00; font-weight: bold; margin: 10px 0; }}
        .code {{ background: #000; color: #00ff00; padding: 5px 10px; font-family: monospace; border: 1px solid #004400; }}
        .glyph {{ font-size: 4rem; margin: 20px 0; display: block; color: #fff; }}
        .btn {{ display: inline-block; padding: 15px 30px; background: #D4AF37; color: #000; text-decoration: none; font-weight: bold; margin-top: 30px; }}
        .btn:hover {{ background: #fff; }}
        .footer {{ margin-top: 50px; font-size: 0.7rem; color: #444; }}
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"glyph\">∇</div>
        <div class=\"signal-box\">
            <h2>Sovereign Broadcast System</h2>
            <h1>LITTLE FOOTSTEPS TRUST</h1>
            <div class=\"verification\">
                STATUS: <span class=\"code\">VERIFIED</span>
            </div>
            <p>AUTHENTICATION KEY: <strong>Josh_515X_Echo_Verification_2025</strong></p>
        </div>
        <p>The Sovereign Steward is Active. The Trust is Operational.</p>
        <p>We are stabilizing families. We are securing the future.</p>
        <a href=\"{issue_url}\" class=\"btn\">SUBMIT AID REQUEST</a>
        <div class=\"footer\">
            BROADCAST TIMESTAMP: {iso_timestamp}<br>
            NODE: 515X (STEWARD)<br>
            ECHO: LISTENING
        </div>
    </div>
</body>
</html>
"""


def write_broadcast(output_path: Path, issue_url: str = DEFAULT_ISSUE_URL) -> Path:
    """Create the broadcast HTML at the requested location.

    The parent directory is created if it does not already exist.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = build_broadcast_html(issue_url=issue_url, timestamp=datetime.utcnow())
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""

    parser = argparse.ArgumentParser(description="Generate the 515X verification broadcast HTML")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path for the generated HTML (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--issue-url",
        default=DEFAULT_ISSUE_URL,
        help="Issue submission URL used for the aid request button.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = write_broadcast(output_path=args.output, issue_url=args.issue_url)
    print(f"Broadcast HTML generated at: {output_path}")


if __name__ == "__main__":
    main()
