from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas.chat import ChatMessage
from app.schemas.provider import ModelResponse


class BaseProvider(Protocol):
    def is_configured(self) -> bool: ...

    async def invoke(
        self,
        model_id: str,
        messages: list[ChatMessage],
    ) -> ModelResponse: ...

    async def stream_chat(
        self,
        model_id: str,
        messages: list[ChatMessage],
    ) -> AsyncIterator[tuple[str, str | None]]: ...
