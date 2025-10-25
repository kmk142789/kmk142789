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
