from typing import Literal, Self

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 10_000
MAX_CONVERSATION_MESSAGES = 50


def guard_message_content(content: str) -> tuple[str, bool]:
    """Truncate content that exceeds schema limits before constructing ChatMessage."""
    if len(content) <= MAX_MESSAGE_CHARS:
        return content, False
    truncated = content[: MAX_MESSAGE_CHARS - 40].rstrip() + "\n\n[truncated to fit message limit]"
    return truncated, True


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS)

    @classmethod
    def create(cls, role: Literal["system", "user", "assistant"], content: str) -> Self:
        safe_content, _ = guard_message_content(content)
        return cls(role=role, content=safe_content)


class ChatRequest(BaseModel):
    model_id: str = Field(alias="modelId")
    messages: list[ChatMessage] = Field(max_length=MAX_CONVERSATION_MESSAGES)

    model_config = {"populate_by_name": True}
