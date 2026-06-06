from collections.abc import AsyncIterator

from app.models.registry import get_model
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.chat import ChatMessage
from app.schemas.consulate import ConsulateStreamEvent
from app.utils.errors import CLIENT_ERROR_MESSAGE
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SingleModelOrchestrator:
    def __init__(self, provider: NvidiaProvider) -> None:
        self._provider = provider

    async def stream(
        self, model_id: str, messages: list[ChatMessage]
    ) -> AsyncIterator[ConsulateStreamEvent]:
        if not get_model(model_id):
            yield ConsulateStreamEvent(
                type="error", message=f"Model not available: {model_id}"
            )
            return

        if not self._provider.is_configured():
            yield ConsulateStreamEvent(type="error", message=CLIENT_ERROR_MESSAGE)
            return

        try:
            async for content, reasoning in self._provider.stream_chat(
                model_id, messages
            ):
                if content:
                    yield ConsulateStreamEvent(type="chunk", content=content)
                if reasoning:
                    yield ConsulateStreamEvent(type="reasoning_chunk", content=reasoning)
            yield ConsulateStreamEvent(type="done")
        except Exception as exc:
            logger.error("Direct chat failed for model %s: %s", model_id, exc)
            yield ConsulateStreamEvent(type="error", message=CLIENT_ERROR_MESSAGE)
