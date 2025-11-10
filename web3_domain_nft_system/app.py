"""Flask application factory for the Web3 Domain NFT service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from flask import Flask, Response, send_from_directory
from flask_cors import CORS

from .src.models import db
from .src.routes import crypto_bp, nft_bp, user_bp

_DEFAULT_SECRET = "asdf#FGSgvasgf$5$WGT"


def _resolve_static_folder(base_path: Path) -> Optional[Path]:
    """Return the static assets directory when it exists."""

    static_dir = base_path / "static"
    return static_dir if static_dir.exists() else None


def create_app(*, database_path: Path | str | None = None) -> Flask:
    """Create and configure a Flask application instance."""

    package_root = Path(__file__).resolve().parent
    static_dir = _resolve_static_folder(package_root)
    database_path = Path(database_path or package_root / "database" / "app.db")
    database_path.parent.mkdir(parents=True, exist_ok=True)

    app = Flask(__name__, static_folder=str(static_dir) if static_dir else None)
    app.config.update(
        SECRET_KEY=os.getenv("WEB3_DOMAIN_APP_SECRET", _DEFAULT_SECRET),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    CORS(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(crypto_bp, url_prefix="/api/crypto")
    app.register_blueprint(nft_bp, url_prefix="/api/nft")

    if static_dir:
        _attach_static_routes(app, static_dir)

    return app


def _attach_static_routes(app: Flask, static_dir: Path) -> None:
    """Register routes that serve the static frontend bundle."""

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_static(path: str) -> Response | tuple[str, int]:
        target = static_dir / path
        if path and target.exists():
            return send_from_directory(app.static_folder or str(static_dir), path)

        index_path = static_dir / "index.html"
        if index_path.exists():
            return send_from_directory(app.static_folder or str(static_dir), "index.html")

        return "Static asset not found", 404


__all__ = ["create_app"]


if __name__ == "__main__":  # pragma: no cover
    create_app().run(host="0.0.0.0", port=5001, debug=True)
