from __future__ import annotations

from typing import Any, TypedDict

class ChatRequestRequired(TypedDict):
    message: str

class ChatRequestOptional(TypedDict, total=False):
    inputs: dict[str, Any]
    execute: bool

class ChatRequest(ChatRequestRequired, ChatRequestOptional):
    """Typed mapping generated from the OpenAPI schema."""
    pass

class ChatResponseRequired(TypedDict):
    function: str
    message: str
    data: dict[str, Any]
    metadata: dict[str, Any]

class ChatResponseOptional(TypedDict, total=False):
    pass

class ChatResponse(ChatResponseRequired, ChatResponseOptional):
    """Typed mapping generated from the OpenAPI schema."""
    pass

class FunctionDescriptionRequired(TypedDict):
    name: str
    description: str
    parameters: dict[str, Any]
    metadata: dict[str, Any]

class FunctionDescriptionOptional(TypedDict, total=False):
    pass

class FunctionDescription(FunctionDescriptionRequired, FunctionDescriptionOptional):
    """Typed mapping generated from the OpenAPI schema."""
    pass

class FunctionListResponseRequired(TypedDict):
    functions: list[FunctionDescription]

class FunctionListResponseOptional(TypedDict, total=False):
    pass

class FunctionListResponse(FunctionListResponseRequired, FunctionListResponseOptional):
    """Typed mapping generated from the OpenAPI schema."""
    pass
