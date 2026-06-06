from collections.abc import AsyncIterator

from app.config.constants import CONSENSUS_WITH_MINORITY_PROMPT, DEADLOCK_SYNTHESIS_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from app.orchestrator.consensus.models import ConsensusResult
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.chat import ChatMessage
from app.schemas.consulate import ConsulateStreamEvent
from app.schemas.provider import ModelResponse
from app.models.registry import get_model
from app.utils.errors import ModelNotFoundError


class Synthesizer:
    def __init__(self, provider: NvidiaProvider) -> None:
        self._provider = provider

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

        summary_parts = []
        for resp in responses:
            text = resp.effective_content
            if resp.success and text:
                header = f"--- {resp.model_name} ({resp.role}) ---"
                summary_parts.append(f"{header}\n{text}")

        consensus_context = ""
        if consensus and not consensus.is_deadlock:
            minority_note = ""
            if consensus.minority_support > 0 and consensus.disagreement:
                d = consensus.disagreement
                minority_note = (
                    f"\nMinority position ({consensus.minority_support * 100:.0f}% support): "
                    f"{d.minority_position}\n"
                    f"Disputed concept: {d.disputed_concept}\n"
                    f"Why: {d.explanation}\n"
                )
            consensus_context = (
                f"\nConsensus Analysis:\n"
                f"- Agreement: {consensus.agreement_score * 100:.0f}%\n"
                f"- Majority ({consensus.majority_support * 100:.0f}%): "
                f"{consensus.clusters[0].position_label if consensus.clusters else 'consensus'}\n"
                f"- Supporting models: {', '.join(consensus.supporting_models)}\n"
                f"{minority_note}"
            )

        system_prompt = (
            CONSENSUS_WITH_MINORITY_PROMPT
            if consensus and consensus.minority_support > 0
            else SYNTHESIS_SYSTEM_PROMPT
        )

        user_content = (
            f"User Question:\n{prompt}\n\n"
            f"Council Responses:\n\n{chr(10).join(summary_parts)}"
            f"{consensus_context}\n\n"
            "Synthesize these responses into a single consensus answer."
        )

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_content),
        ]

        full = ""
        async for content, _reasoning in self._provider.stream_chat(
            synthesis_model_id, messages
        ):
            if content:
                full += content
                yield ConsulateStreamEvent(type="synthesis_chunk", content=content)

        yield ConsulateStreamEvent(type="synthesis_complete", content=full)

    async def stream_deadlock_summary(
        self,
        prompt: str,
        majority: str,
        minority: str,
        agreement_score: float,
        synthesis_model_id: str,
    ) -> AsyncIterator[ConsulateStreamEvent]:
        if not get_model(synthesis_model_id):
            raise ModelNotFoundError(
                f"Synthesis model not found: {synthesis_model_id}"
            )
        user_content = (
            f"User Question:\n{prompt}\n\n"
            f"Agreement Score: {agreement_score:.2f} (DEADLOCK — no majority position)\n\n"
            f"MAJORITY POSITION:\n{majority}\n\n"
            f"MINORITY POSITION:\n{minority}\n\n"
            "Present the deadlock transparently to the user."
        )

        messages = [
            ChatMessage(role="system", content=DEADLOCK_SYNTHESIS_PROMPT),
            ChatMessage(role="user", content=user_content),
        ]

        full = ""
        async for content, _reasoning in self._provider.stream_chat(
            synthesis_model_id, messages
        ):
            if content:
                full += content
                yield ConsulateStreamEvent(type="synthesis_chunk", content=content)

        yield ConsulateStreamEvent(type="synthesis_complete", content=full)
