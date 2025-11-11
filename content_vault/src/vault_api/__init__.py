"""Vault API package exposing the HTTP server entrypoint and routing helpers."""

from .main import build_server, serve_forever

__all__ = ["build_server", "serve_forever"]
