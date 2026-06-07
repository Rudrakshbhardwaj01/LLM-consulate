from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

MAX_MESSAGE_CHARS = 10_000
MAX_CONVERSATION_MESSAGES = 50


def guard_message_content(content: str) -> tuple[str, bool]:
    """Truncate content that exceeds schema limits before constructing ChatMessage."""
    if not isinstance(content, str):
        content = str(content)
    if len(content) <= MAX_MESSAGE_CHARS:
        return content, False
    suffix = "\n\n[truncated to fit message limit]"
    truncated = content[: MAX_MESSAGE_CHARS - len(suffix)].rstrip() + suffix
    return truncated[:MAX_MESSAGE_CHARS], True


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS)

    @model_validator(mode="before")
    @classmethod
    def enforce_content_limit(cls, data: Any) -> Any:
        if isinstance(data, dict) and "content" in data:
            safe_content, _ = guard_message_content(data["content"])
            data = {**data, "content": safe_content}
        return data

    @classmethod
    def create(cls, role: Literal["system", "user", "assistant"], content: str) -> Self:
        safe_content, _ = guard_message_content(content)
        return cls(role=role, content=safe_content)


class ChatRequest(BaseModel):
    model_id: str = Field(alias="modelId")
    messages: list[ChatMessage] = Field(max_length=MAX_CONVERSATION_MESSAGES)

    model_config = {"populate_by_name": True}
