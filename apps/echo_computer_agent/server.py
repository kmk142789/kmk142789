"""FastAPI deployment surface for the Echo chat agent."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from echo.chat_agent import EchoChatAgent


def create_agent() -> EchoChatAgent:
    """Factory returning a configured :class:`EchoChatAgent` instance."""

    return EchoChatAgent()


agent = create_agent()
app = FastAPI(
    title="Echo Computer Assistant Agent",
    version="1.0.0",
    description="Chat-oriented API that routes commands to the Echo ecosystem.",
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User command or query for the agent.")
    inputs: Dict[str, Any] | None = Field(
        default=None,
        description="Optional inputs passed to the selected backend function.",
    )
    execute: bool = Field(
        default=False,
        description="When true the agent will execute the matched backend function.",
    )


class ChatResponse(BaseModel):
    function: str
    message: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


@app.get("/functions")
def list_functions() -> Dict[str, Any]:
    """Return the available function call specifications."""

    return {"functions": list(agent.describe_functions())}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Handle a chat request and return the agent response."""

    response = agent.handle_command(
        request.message,
        inputs=request.inputs or {},
        execute=request.execute,
    )
    payload = response.to_payload()
    return ChatResponse(**payload)


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    try:
        import uvicorn
    except ModuleNotFoundError:  # pragma: no cover - uvicorn optional
        raise SystemExit(
            "uvicorn is required to launch the chat agent server. Install with `pip install uvicorn`."
        )

    uvicorn.run("apps.echo_computer_agent.server:app", host="0.0.0.0", port=8000)
