"""Blueprint exposing NFT minting routes for the Web3 domain service."""

from __future__ import annotations

from flask import Blueprint
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from apps.web3_domain_nft_system import NFTMinter


def create_nft_blueprint(minter: "NFTMinter" | None = None) -> Blueprint:
    """Return a blueprint that proxies to :mod:`apps.web3_domain_nft_system`."""

    from apps.web3_domain_nft_system.nft_minter import create_blueprint as shared_blueprint

    return shared_blueprint(minter)


# Default blueprint used by the API package.  Individual applications can
# construct their own blueprint via :func:`create_nft_blueprint` when they need
# to customise the underlying :class:`~apps.web3_domain_nft_system.NFTMinter`.
nft_bp = create_nft_blueprint()

__all__ = ["create_nft_blueprint", "nft_bp"]
