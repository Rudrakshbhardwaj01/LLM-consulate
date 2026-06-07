import asyncio
import time
from collections.abc import AsyncIterator

from app.config.settings import Settings
from app.models.registry import DEFAULT_SYNTHESIS_MODEL_ID, get_council_members, get_model
from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.synthesis_prompt import (
    build_consensus_fallback,
    build_structured_deadlock_fallback,
)
from app.orchestrator.synthesizer import Synthesizer
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.chat import ChatMessage
from app.schemas.consulate import ConsulateStreamEvent
from app.schemas.provider import ModelResponse
from app.utils.errors import CLIENT_ERROR_MESSAGE
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ConsulateOrchestrator:
    def __init__(
        self,
        provider: NvidiaProvider,
        synthesizer: Synthesizer,
        settings: Settings,
    ) -> None:
        self._provider = provider
        self._synthesizer = synthesizer
        self._settings = settings

    async def _collect_model_stream(
        self,
        model_id: str,
        messages: list[ChatMessage],
        queue: asyncio.Queue[ConsulateStreamEvent | None],
    ) -> tuple[str, str | None]:
        content_parts: list[str] = []
        reasoning_parts: list[str] = []

        async for content, reasoning in self._provider.stream_chat(model_id, messages):
            if content:
                content_parts.append(content)
                await queue.put(
                    ConsulateStreamEvent(
                        type="model_chunk",
                        model_id=model_id,
                        content=content,
                    )
                )
            if reasoning:
                reasoning_parts.append(reasoning)
                await queue.put(
                    ConsulateStreamEvent(
                        type="model_chunk",
                        model_id=model_id,
                        reasoning=reasoning,
                    )
                )

        return "".join(content_parts), ("".join(reasoning_parts) or None)

    async def _invoke_with_streaming(
        self,
        model_id: str,
        messages: list[ChatMessage],
        queue: asyncio.Queue[ConsulateStreamEvent | None],
    ) -> ModelResponse:
        model = get_model(model_id)
        model_name = model.display_name if model else model_id
        role = model.role if model else ""
        timeout_s, timeout_source = self._settings.council_timeout_info()

        logger.info(
            "consulate.model.start | model=%s | timeout=%.1fs | source=%s",
            model_id,
            timeout_s,
            timeout_source,
        )
        start = time.perf_counter()

        await queue.put(
            ConsulateStreamEvent(
                type="model_status", model_id=model_id, model_status="streaming"
            )
        )

        try:
            full_content, full_reasoning = await asyncio.wait_for(
                self._collect_model_stream(model_id, messages, queue),
                timeout=timeout_s,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)

            logger.info(
                "consulate.model.complete | model=%s | latency_ms=%d | content_chars=%d | reasoning_chars=%d",
                model_id,
                latency_ms,
                len(full_content),
                len(full_reasoning or ""),
            )

            await queue.put(
                ConsulateStreamEvent(
                    type="model_complete",
                    model_id=model_id,
                    content=full_content,
                    reasoning=full_reasoning,
                    latency_ms=latency_ms,
                )
            )
            await queue.put(
                ConsulateStreamEvent(
                    type="model_status", model_id=model_id, model_status="complete"
                )
            )

            return ModelResponse(
                modelId=model_id,
                modelName=model_name,
                role=role,
                content=full_content,
                reasoning=full_reasoning,
                latencyMs=latency_ms,
                success=True,
            )

        except TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            error_msg = f"Timed out after {timeout_s:.0f}s"
            logger.warning(
                "consulate.model.timeout | model=%s | latency_ms=%d | limit=%ss",
                model_id,
                latency_ms,
                timeout_s,
            )
            await queue.put(
                ConsulateStreamEvent(
                    type="model_error",
                    model_id=model_id,
                    error=CLIENT_ERROR_MESSAGE,
                )
            )
            await queue.put(
                ConsulateStreamEvent(
                    type="model_status", model_id=model_id, model_status="timeout"
                )
            )
            return ModelResponse(
                modelId=model_id,
                modelName=model_name,
                role=role,
                latencyMs=latency_ms,
                success=False,
                error=error_msg,
            )

        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "consulate.model.error | model=%s | latency_ms=%d | error=%s",
                model_id,
                latency_ms,
                exc,
            )
            await queue.put(
                ConsulateStreamEvent(
                    type="model_error", model_id=model_id, error=CLIENT_ERROR_MESSAGE
                )
            )
            await queue.put(
                ConsulateStreamEvent(
                    type="model_status", model_id=model_id, model_status="error"
                )
            )
            return ModelResponse(
                modelId=model_id,
                modelName=model_name,
                role=role,
                latencyMs=latency_ms,
                success=False,
                error=CLIENT_ERROR_MESSAGE,
            )

    async def stream(
        self,
        model_ids: list[str],
        messages: list[ChatMessage],
        prompt: str,
        synthesis_model_id: str | None = None,
    ) -> AsyncIterator[ConsulateStreamEvent]:
        council_ids = model_ids or [m.id for m in get_council_members()]
        synthesis_id = synthesis_model_id or self._settings.synthesis_model_id or DEFAULT_SYNTHESIS_MODEL_ID

        logger.info(
            "consulate.session.start | council=%s | synthesis=%s | members=%d",
            council_ids,
            synthesis_id,
            len(council_ids),
        )

        yield ConsulateStreamEvent(type="stage", stage="initializing")

        user_messages = [*messages, ChatMessage.create("user", prompt)]

        yield ConsulateStreamEvent(type="stage", stage="receiving")

        for model_id in council_ids:
            yield ConsulateStreamEvent(
                type="model_status", model_id=model_id, model_status="pending"
            )

        queue: asyncio.Queue[ConsulateStreamEvent | None] = asyncio.Queue()
        results: list[ModelResponse] = []

        async def run_member(model_id: str) -> ModelResponse:
            return await self._invoke_with_streaming(model_id, user_messages, queue)

        async def gather_council() -> None:
            gathered = await asyncio.gather(
                *[run_member(mid) for mid in council_ids],
                return_exceptions=True,
            )
            for item in gathered:
                if isinstance(item, ModelResponse):
                    results.append(item)
                elif isinstance(item, Exception):
                    logger.error("Council gather exception: %s", item)
            await queue.put(None)

        gather_task = asyncio.create_task(gather_council())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

        await gather_task

        successful = [r for r in results if r.success and r.effective_content]
        for resp in successful:
            logger.info(
                "consulate.council.response | model=%s | latency_ms=%d | content_chars=%d",
                resp.model_id,
                resp.latency_ms,
                len(resp.effective_content),
            )
        timed_out = [r for r in results if r.error and "Timed out" in (r.error or "")]
        failed_count = len(council_ids) - len(successful)

        logger.info(
            "consulate.council.done | successful=%d | timed_out=%d | failed=%d",
            len(successful),
            len(timed_out),
            failed_count - len(timed_out),
        )

        if len(successful) < max(1, len(council_ids) // 2):
            yield ConsulateStreamEvent(type="stage", stage="error")
            yield ConsulateStreamEvent(
                type="error",
                message=(
                    f"Insufficient council responses ({len(successful)} of {len(council_ids)}). "
                    "At least half the council must respond."
                ),
            )
            return

        yield ConsulateStreamEvent(
            type="council_summary",
            council_total=len(council_ids),
            council_responded=len(successful),
            message=(
                f"{len(successful)} of {len(council_ids)} council members responded"
                if failed_count
                else None
            ),
        )

        yield ConsulateStreamEvent(type="stage", stage="analyzing")

        engine = AgreementEngine(
            provider=self._provider,
            judge_model_id=self._settings.judge_model_id,
            embedding_model_id=self._settings.embedding_model_id,
            use_llm_claims=(
                self._settings.agreement_use_llm_claims or self._settings.agreement_use_llm
            ),
            use_llm_judge=(
                self._settings.agreement_use_llm_judge or self._settings.agreement_use_llm
            ),
            use_embeddings_api=self._settings.agreement_use_embeddings,
        )
        agreement = await engine.analyze(successful, prompt)

        logger.info(
            "consulate.agreement | score=%.3f | outcome=%s | vote_support=%.0f%% | deadlock=%s",
            agreement.agreement_score,
            agreement.consensus_outcome,
            agreement.majority_support * 100,
            agreement.is_deadlock,
        )

        yield ConsulateStreamEvent(
            type="agreement_analysis",
            agreement_score=agreement.agreement_score,
            majority_support=agreement.majority_support,
            minority_support=agreement.minority_support,
            supporting_models=agreement.supporting_models,
            minority_models=agreement.minority_models,
            primary_disagreement=agreement.primary_disagreement,
            disagreement=agreement.disagreement,
            is_consensus=not agreement.is_deadlock,
            consensus_outcome=agreement.consensus_outcome,
            outcome_label=agreement.outcome_label,
            confidence_level=agreement.confidence_level,
        )

        for report in agreement.minority_reports:
            yield ConsulateStreamEvent(
                type="minority_report",
                minority_report=report,
            )

        if agreement.is_deadlock:
            logger.warning(
                "consulate.deadlock | agreement=%.2f", agreement.agreement_score
            )

            yield ConsulateStreamEvent(
                type="deadlock",
                stage="deadlock",
                agreement_score=agreement.agreement_score,
                majority_position=agreement.majority_position,
                minority_position=agreement.minority_position,
                primary_disagreement=agreement.primary_disagreement,
                majority_support=agreement.majority_support,
                minority_support=agreement.minority_support,
                supporting_models=agreement.supporting_models,
                minority_models=agreement.minority_models,
                disagreement=agreement.disagreement,
                is_consensus=False,
                consensus_outcome=agreement.consensus_outcome,
                outcome_label=agreement.outcome_label,
                confidence_level=agreement.confidence_level,
                message="Council Deadlocked",
            )

            fallback_answer = build_structured_deadlock_fallback(agreement)
            synthesis_start = time.perf_counter()
            try:
                logger.info(
                    "consulate.synthesis.start | mode=deadlock | model=%s",
                    synthesis_id,
                )
                async for event in self._synthesizer.stream_deadlock_summary(
                    prompt,
                    agreement,
                    synthesis_id,
                    successful,
                ):
                    yield event
                logger.info(
                    "consulate.synthesis.complete | mode=deadlock | latency_ms=%d",
                    int((time.perf_counter() - synthesis_start) * 1000),
                )
                yield ConsulateStreamEvent(type="stage", stage="deadlock")
            except Exception as exc:
                logger.error(
                    "consulate.synthesis.error | mode=deadlock | error=%s | synthesis.fallback_used=true",
                    exc,
                )
                yield ConsulateStreamEvent(
                    type="synthesis_complete",
                    content=fallback_answer,
                    answer=fallback_answer,
                    synthesis_status="degraded",
                    deadlock=True,
                    synthesis_degraded=True,
                )
                yield ConsulateStreamEvent(type="stage", stage="deadlock")
            return

        yield ConsulateStreamEvent(type="stage", stage="synthesizing")

        fallback_answer = build_consensus_fallback(agreement, successful)
        synthesis_start = time.perf_counter()
        try:
            logger.info(
                "consulate.synthesis.start | mode=consensus | model=%s | inputs=%d",
                synthesis_id,
                len(successful),
            )
            async for event in self._synthesizer.stream_consensus(
                prompt,
                successful,
                synthesis_id,
                consensus=agreement,
            ):
                yield event
            logger.info(
                "consulate.synthesis.complete | mode=consensus | latency_ms=%d",
                int((time.perf_counter() - synthesis_start) * 1000),
            )
            yield ConsulateStreamEvent(type="stage", stage="complete")
        except Exception as exc:
            logger.error(
                "consulate.synthesis.error | mode=consensus | error=%s | synthesis.fallback_used=true",
                exc,
            )
            yield ConsulateStreamEvent(
                type="synthesis_complete",
                content=fallback_answer,
                answer=fallback_answer,
                synthesis_status="degraded",
                deadlock=False,
                synthesis_degraded=True,
            )
            yield ConsulateStreamEvent(type="stage", stage="complete")
