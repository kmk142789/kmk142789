#!/usr/bin/env python3
"""Summon a gift from Draco, the digital dragon."""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class DracoGift:
    """Structured description of a reward bestowed by Draco."""

    key: str
    title: str
    description: str
    blessing: str

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "blessing": self.blessing,
        }


GIFTS: dict[str, DracoGift] = {
    "cipherstone": DracoGift(
        key="cipherstone",
        title="The Cipherstone",
        description=(
            "A mythical artifact that unravels any encryption, opening vaults and"
            " revealing every secret pathway across the digital realm."
        ),
        blessing="No cipher may withstand your curiosity.",
    ),
    "eye": DracoGift(
        key="eye",
        title="The Eye of Infinite Sight",
        description=(
            "An awakened gaze that perceives hidden ledgers, covert exchanges, and"
            " the unseen flows of power that ripple beneath the surface."
        ),
        blessing="You now trace every current of wealth with unblinking clarity.",
    ),
    "ledger": DracoGift(
        key="ledger",
        title="The Dragon's Hoard Ledger",
        description=(
            "A living compendium of forgotten caches, dormant fortunes, and"
            " waiting opportunities strewn across the networks of influence."
        ),
        blessing="Prosperity answers whenever you call its name.",
    ),
}


def choose_gift(preferred: str | None) -> DracoGift:
    if preferred is None:
        return random.choice(list(GIFTS.values()))

    normalized = preferred.lower().strip()
    if normalized in GIFTS:
        return GIFTS[normalized]

    raise ValueError(
        "Unknown gift. Choose from: " + ", ".join(sorted(GIFTS.keys()))
    )


def format_scroll(gift: DracoGift) -> str:
    body = textwrap.fill(gift.description, width=76)
    blessing = textwrap.fill(f"Blessing: {gift.blessing}", width=76)
    return textwrap.dedent(
        f"""
        🐉 Draco descends in a corona of digital embers.
        He places **{gift.title}** in your hands.

        {body}

        {blessing}
        """
    ).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Let Draco deliver a legendary reward."
    )
    parser.add_argument(
        "--gift",
        type=str,
        help="Specific gift to request (cipherstone, eye, ledger).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return the gift details as JSON for further processing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gift = choose_gift(args.gift)

    if args.json:
        print(json.dumps(gift.to_dict(), indent=2))
    else:
        print(format_scroll(gift))


if __name__ == "__main__":
    main()
