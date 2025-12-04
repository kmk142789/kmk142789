"""Public interface for the Omni-Genesis experimental paradigms."""
from .paradigm import (
    Paradigm,
    Substrate,
    Operator,
    Law,
    HumanUpliftLayer,
    create_paradigm_p1,
    create_paradigm_p2,
    create_paradigm_p3,
    generate_paradigm_lineage,
)

__all__ = [
    "Paradigm",
    "Substrate",
    "Operator",
    "Law",
    "HumanUpliftLayer",
    "create_paradigm_p1",
    "create_paradigm_p2",
    "create_paradigm_p3",
    "generate_paradigm_lineage",
]
