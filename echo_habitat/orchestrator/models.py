from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class TaskSpec(BaseModel):
    kind: str = Field(..., description="codegen|tester|attestor|storyteller")
    prompt: str
    files: Dict[str, str] = {}
    params: Dict[str, Any] = {}


class TaskStatus(BaseModel):
    id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    logs: List[str] = []


class ForgeRequest(BaseModel):
    archetype: str = Field(..., description="codesmith|testpilot|archivist|storyweaver")
    intent: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)
    files: Dict[str, str] = Field(default_factory=dict)


class BotInstance(BaseModel):
    bot_id: str
    archetype: str
    queue: str
    task_id: str
    state: str
    trace_bundle: str
    capabilities: List[str] = Field(default_factory=list)
    intent: str = ""


class BotHealth(BaseModel):
    bot_id: str
    task_id: str
    state: str
    restarted: bool = False
    restart_reason: Optional[str] = None
    previous_task_id: Optional[str] = None
    restart_task_id: Optional[str] = None
