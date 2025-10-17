"""Seed helpers for populating the atlas with demo data."""

from __future__ import annotations

from ..domain import Edge, EntityType, Node, RelationType
from ..utils import slugify

SEED_ENTITIES = (
    Node(
        identifier=slugify("person", "kmk142789"),
        name="kmk142789",
        entity_type=EntityType.PERSON,
        metadata={"handle": "@kmk142789", "role": "Maintainer"},
    ),
    Node(
        identifier=slugify("service", "echo-repo"),
        name="Echo Repository",
        entity_type=EntityType.REPO,
        metadata={"path": "https://github.com/echo-project"},
    ),
    Node(
        identifier=slugify("service", "cloudflare"),
        name="Cloudflare",
        entity_type=EntityType.SERVICE,
        metadata={"category": "CDN"},
    ),
    Node(
        identifier=slugify("service", "firebase"),
        name="Firebase",
        entity_type=EntityType.SERVICE,
        metadata={"category": "Backend"},
    ),
    Node(
        identifier=slugify("service", "vercel"),
        name="Vercel",
        entity_type=EntityType.SERVICE,
        metadata={"category": "Hosting"},
    ),
)

SEED_RELATIONS = (
    Edge(
        identifier=slugify("owns", "kmk142789", "echo"),
        source=SEED_ENTITIES[0].identifier,
        target=SEED_ENTITIES[1].identifier,
        relation=RelationType.OWNS,
        metadata={"confidence": "seed"},
    ),
    Edge(
        identifier=slugify("deploys", "echo", "vercel"),
        source=SEED_ENTITIES[1].identifier,
        target=SEED_ENTITIES[4].identifier,
        relation=RelationType.DEPLOYS,
        metadata={"environment": "production"},
    ),
    Edge(
        identifier=slugify("connects", "echo", "cloudflare"),
        source=SEED_ENTITIES[1].identifier,
        target=SEED_ENTITIES[2].identifier,
        relation=RelationType.CONNECTS_TO,
    ),
    Edge(
        identifier=slugify("connects", "echo", "firebase"),
        source=SEED_ENTITIES[1].identifier,
        target=SEED_ENTITIES[3].identifier,
        relation=RelationType.CONNECTS_TO,
    ),
)


def load_seed(repository) -> None:
    for node in SEED_ENTITIES:
        repository.upsert_node(node)
    for edge in SEED_RELATIONS:
        repository.upsert_edge(edge)
