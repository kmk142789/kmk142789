"""Atlas API routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from echo_atlas.models import AtlasEdge, AtlasNode, EntityType, RelationType
from echo_atlas.services import AtlasService

router = APIRouter()
_service = AtlasService()
_service.seed_demo_data()


class NodeModel(BaseModel):
    id: str
    name: str
    entity_type: EntityType
    attributes: dict = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_node(cls, node: AtlasNode) -> "NodeModel":
        return cls(**node.as_dict())


class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    relation: RelationType
    attributes: dict = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_edge(cls, edge: AtlasEdge) -> "EdgeModel":
        return cls(**edge.as_dict())


class SummaryModel(BaseModel):
    nodes: dict
    edges: dict
    total_nodes: int
    total_edges: int
    recent_changes: List[dict]


class WebhookEvent(BaseModel):
    type: str
    entity_type: EntityType | None = None
    name: str | None = None
    identifier: str | None = None
    attributes: dict = Field(default_factory=dict)
    source: str | None = None
    target: str | None = None
    relation: RelationType | None = None


class WebhookPayload(BaseModel):
    events: List[WebhookEvent]


class WebhookResponse(BaseModel):
    accepted: int


def get_service() -> AtlasService:
    return _service


async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@router.get("/atlas/nodes", response_model=List[NodeModel])
async def atlas_nodes(service: AtlasService = Depends(get_service)) -> List[NodeModel]:
    return [NodeModel.from_node(node) for node in service.repository.iter_nodes()]


@router.get("/atlas/edges", response_model=List[EdgeModel])
async def atlas_edges(service: AtlasService = Depends(get_service)) -> List[EdgeModel]:
    return [EdgeModel.from_edge(edge) for edge in service.repository.iter_edges()]


@router.get("/atlas/summary", response_model=SummaryModel)
async def atlas_summary(service: AtlasService = Depends(get_service)) -> SummaryModel:
    return SummaryModel(**service.query.summary_snapshot())


def verify_signature(signature: str | None, payload: WebhookPayload) -> None:
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Atlas-Signature header")
    # Stub verification: log only
    if len(signature) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")


@router.post("/hooks/atlas", response_model=WebhookResponse)
async def atlas_webhook(
    payload: WebhookPayload,
    signature: str | None = Header(default=None, alias="X-Atlas-Signature"),
    service: AtlasService = Depends(get_service),
) -> WebhookResponse:
    verify_signature(signature, payload)
    accepted = 0
    for event in payload.events:
        if event.type == "node":
            if not event.name or not event.entity_type:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node events require name and entity_type")
            identifier = event.identifier or f"{event.entity_type.value}:{event.name.lower().replace(' ', '-')}"
            node = AtlasNode(
                identifier=identifier,
                name=event.name,
                entity_type=event.entity_type,
                attributes=event.attributes,
            )
            service.repository.upsert_node(node)
            accepted += 1
        elif event.type == "edge":
            if not (event.source and event.target and event.relation):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Edge events require source, target, relation")
            edge = service.repository.ensure_edge(event.source, event.relation, event.target, attributes=event.attributes)
            accepted += 1
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event type: {event.type}")
    return WebhookResponse(accepted=accepted)
