from collections.abc import AsyncIterator

from app.config.constants import CONSENSUS_WITH_MINORITY_PROMPT, DEADLOCK_SYNTHESIS_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from app.orchestrator.consensus.models import ConsensusResult
from app.orchestrator.message_guard import assert_messages_within_limit
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

    def _prepare_messages(
        self,
        mode: str,
        system_prompt: str,
        user_content: str,
        meta: dict[str, int | bool],
    ) -> list:
        raw_len = int(meta.get("raw_chars", 0))
        compressed_len = int(meta.get("compressed_chars", len(user_content)))
        logger.info(
            "consulate.synthesis.prompt | mode=%s | len(prompt)=%d | len(compressed_prompt)=%d | "
            "synthesis.prompt_chars=%d | synthesis.compressed_chars=%d | synthesis.truncated=%s",
            mode,
            raw_len,
            compressed_len,
            len(user_content),
            compressed_len,
            meta.get("truncated", False),
        )

        messages = [
            safe_chat_message("system", system_prompt),
            safe_chat_message("user", user_content),
        ]
        assert_messages_within_limit(messages)
        return messages

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
        messages = self._prepare_messages("consensus", system_prompt, user_content, meta)

        full = ""
        async for content, _reasoning in self._provider.stream_chat(
            synthesis_model_id, messages
        ):
            if content:
                full += content
                yield ConsulateStreamEvent(type="synthesis_chunk", content=content)

        yield ConsulateStreamEvent(
            type="synthesis_complete", content=full, synthesis_status="ok"
        )

    async def stream_deadlock_summary(
        self,
        prompt: str,
        consensus: ConsensusResult,
        synthesis_model_id: str,
        responses: list[ModelResponse] | None = None,
    ) -> AsyncIterator[ConsulateStreamEvent]:
        if not get_model(synthesis_model_id):
            raise ModelNotFoundError(
                f"Synthesis model not found: {synthesis_model_id}"
            )

        user_content, meta = build_deadlock_user_content(prompt, consensus, responses)
        messages = self._prepare_messages(
            "deadlock", DEADLOCK_SYNTHESIS_PROMPT, user_content, meta
        )

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
            synthesis_status="ok",
            deadlock=True,
        )
