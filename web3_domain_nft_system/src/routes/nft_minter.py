"""Blueprint exposing NFT minting routes for the Web3 domain service."""

from __future__ import annotations

from flask import Blueprint

from apps.web3_domain_nft_system import (  # noqa: WPS347 - shared implementation
    NFTMinter,
    create_blueprint as _create_nft_blueprint,
)


def create_nft_blueprint(minter: NFTMinter | None = None) -> Blueprint:
    """Return a blueprint that proxies to :mod:`apps.web3_domain_nft_system`."""

    return _create_nft_blueprint(minter)


# Default blueprint used by the API package.  Individual applications can
# construct their own blueprint via :func:`create_nft_blueprint` when they need
# to customise the underlying :class:`~apps.web3_domain_nft_system.NFTMinter`.
nft_bp = create_nft_blueprint()

__all__ = ["create_nft_blueprint", "nft_bp"]
