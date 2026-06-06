from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 10_000
MAX_CONVERSATION_MESSAGES = 50


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    model_id: str = Field(alias="modelId")
    messages: list[ChatMessage] = Field(max_length=MAX_CONVERSATION_MESSAGES)

    model_config = {"populate_by_name": True}
