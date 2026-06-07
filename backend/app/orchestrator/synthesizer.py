from collections.abc import AsyncIterator

from app.config.constants import CONSENSUS_WITH_MINORITY_PROMPT, DEADLOCK_SYNTHESIS_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from app.orchestrator.consensus.models import ConsensusResult
from app.orchestrator.synthesis_prompt import (
    build_consensus_user_content,
    build_deadlock_user_content,
    safe_chat_message,
)
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.consulate import ConsulateStreamEvent
from app.schemas.provider import ModelResponse
from app.models.registry import get_model
from app.utils.errors import ModelNotFoundError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class Synthesizer:
    def __init__(self, provider: NvidiaProvider) -> None:
        self._provider = provider

    def _log_prompt_metrics(
        self,
        mode: str,
        meta: dict[str, int | bool],
    ) -> None:
        logger.info(
            "consulate.synthesis.prompt | mode=%s | synthesis.prompt_chars=%d | "
            "synthesis.compressed_chars=%d | synthesis.truncated=%s | compressed=%s",
            mode,
            meta["prompt_chars"],
            meta["compressed_chars"],
            meta["truncated"],
            meta["compressed"],
        )

    async def stream_consensus(
        self,
        prompt: str,
        responses: list[ModelResponse],
        synthesis_model_id: str,
        consensus: ConsensusResult | None = None,
    ) -> AsyncIterator[ConsulateStreamEvent]:
        if not get_model(synthesis_model_id):
            raise ModelNotFoundError(
                f"Synthesis model not found: {synthesis_model_id}"
            )

        system_prompt = (
            CONSENSUS_WITH_MINORITY_PROMPT
            if consensus and consensus.minority_support > 0
            else SYNTHESIS_SYSTEM_PROMPT
        )

        user_content, meta = build_consensus_user_content(prompt, responses, consensus)
        self._log_prompt_metrics("consensus", meta)

        messages = [
            safe_chat_message("system", system_prompt),
            safe_chat_message("user", user_content),
        ]

        full = ""
        async for content, _reasoning in self._provider.stream_chat(
            synthesis_model_id, messages
        ):
            if content:
                full += content
                yield ConsulateStreamEvent(type="synthesis_chunk", content=content)

        yield ConsulateStreamEvent(type="synthesis_complete", content=full, status="ok")

    async def stream_deadlock_summary(
        self,
        prompt: str,
        consensus: ConsensusResult,
        synthesis_model_id: str,
    ) -> AsyncIterator[ConsulateStreamEvent]:
        if not get_model(synthesis_model_id):
            raise ModelNotFoundError(
                f"Synthesis model not found: {synthesis_model_id}"
            )

        user_content, meta = build_deadlock_user_content(prompt, consensus)
        self._log_prompt_metrics("deadlock", meta)

        messages = [
            safe_chat_message("system", DEADLOCK_SYNTHESIS_PROMPT),
            safe_chat_message("user", user_content),
        ]

        full = ""
        async for content, _reasoning in self._provider.stream_chat(
            synthesis_model_id, messages
        ):
            if content:
                full += content
                yield ConsulateStreamEvent(type="synthesis_chunk", content=content)

        yield ConsulateStreamEvent(
            type="synthesis_complete",
            content=full,
            status="ok",
            deadlock=True,
        )
