import asyncio
import time
import uuid
from collections.abc import AsyncIterator

from app.config.settings import Settings
from app.models.registry import DEFAULT_SYNTHESIS_MODEL_ID, get_council_members, get_model
from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.synthesis_prompt import (
    build_consensus_fallback,
    build_consensus_user_content,
    build_deadlock_user_content,
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


def _has_displayable_response(response: ModelResponse) -> bool:
    """Matches UI: model_complete with non-empty raw content."""
    return response.success and bool((response.content or "").strip())


def _count_council_responses(
    results: list[ModelResponse],
) -> dict[str, int]:
    displayed = [r for r in results if _has_displayable_response(r)]
    analysis = [r for r in results if r.success and r.effective_content]
    timed_out = [r for r in results if r.error and "Timed out" in (r.error or "")]
    return {
        "successful": len(displayed),
        "timed_out": len(timed_out),
        "failed": len(results) - len(displayed),
        "displayed": len(displayed),
        "analysis": len(analysis),
    }


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

        async for content, reasoning in self._provider.stream_chat(
            model_id,
            messages,
            max_tokens=self._settings.council_max_tokens,
        ):
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

        session_start = time.perf_counter()
        request_id = uuid.uuid4().hex[:12]

        logger.info(
            "consulate.session.start | request_id=%s | council=%s | synthesis=%s | members=%d",
            request_id,
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

        council_start = time.perf_counter()

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

        council_ms = int((time.perf_counter() - council_start) * 1000)
        logger.info("consulate.timing | stage=council_collection | council_ms=%d", council_ms)

        yield ConsulateStreamEvent(type="stage", stage="analyzing")

        counts = _count_council_responses(results)
        displayed_responses = [r for r in results if _has_displayable_response(r)]
        analysis_responses = [r for r in results if r.success and r.effective_content]

        for resp in displayed_responses:
            logger.info(
                "consulate.council.response | model=%s | latency_ms=%d | content_chars=%d",
                resp.model_id,
                resp.latency_ms,
                len(resp.content or ""),
            )

        logger.info(
            "consulate.council.done | successful=%d | timed_out=%d | failed=%d | analysis=%d",
            counts["successful"],
            counts["timed_out"],
            counts["failed"],
            counts["analysis"],
        )

        if counts["analysis"] < max(1, len(council_ids) // 2):
            yield ConsulateStreamEvent(type="stage", stage="error")
            yield ConsulateStreamEvent(
                type="error",
                message=(
                    f"Insufficient council responses ({counts['analysis']} of {len(council_ids)}). "
                    "At least half the council must respond."
                ),
            )
            return

        yield ConsulateStreamEvent(
            type="council_summary",
            council_total=len(council_ids),
            council_responded=counts["displayed"],
            message=(
                f"{counts['displayed']} of {len(council_ids)} council members responded"
                if counts["displayed"] < len(council_ids)
                else None
            ),
        )

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
        agreement_start = time.perf_counter()
        agreement = await engine.analyze(analysis_responses, prompt, request_id=request_id)
        agreement_ms = int((time.perf_counter() - agreement_start) * 1000)
        agreement_timing = agreement.timing
        claims_ms = agreement_timing.claims_ms if agreement_timing else agreement_ms
        embeddings_ms = agreement_timing.embeddings_ms if agreement_timing else 0
        similarity_ms = agreement_timing.similarity_ms if agreement_timing else 0
        cluster_ms = agreement_timing.cluster_ms if agreement_timing else 0
        majority_ms = agreement_timing.majority_ms if agreement_timing else 0
        judge_ms = agreement_timing.judge_ms if agreement_timing else 0
        if agreement_timing and agreement_timing.agreement_ms:
            agreement_ms = agreement_timing.agreement_ms
        logger.info(
            "consulate.timing | stage=agreement_analysis | agreement_ms=%d | "
            "claims_ms=%d | embeddings_ms=%d | similarity_ms=%d | "
            "cluster_ms=%d | majority_ms=%d | judge_ms=%d",
            agreement_ms,
            claims_ms,
            embeddings_ms,
            similarity_ms,
            cluster_ms,
            majority_ms,
            judge_ms,
        )

        logger.info(
            "consulate.agreement | score=%.3f | outcome=%s | vote_support=%.0f%% | "
            "topic_support=%.0f%% | deadlock=%s",
            agreement.agreement_score,
            agreement.consensus_outcome,
            agreement.majority_support * 100,
            agreement.topic_support * 100,
            agreement.is_deadlock,
        )

        yield ConsulateStreamEvent(
            type="agreement_analysis",
            agreement_score=agreement.agreement_score,
            majority_support=agreement.majority_support,
            minority_support=agreement.minority_support,
            topic_support=agreement.topic_support,
            recommendation_support=agreement.recommendation_support,
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

            logger.info(
                "consulate.response_count | successful=%d | timed_out=%d | failed=%d | displayed=%d | analysis=%d",
                counts["successful"],
                counts["timed_out"],
                counts["failed"],
                counts["displayed"],
                counts["analysis"],
            )

            fallback_answer = build_structured_deadlock_fallback(agreement)
            synthesis_start = time.perf_counter()
            try:
                deadlock_payload, _payload_meta = build_deadlock_user_content(
                    prompt, agreement, analysis_responses
                )
                logger.info(
                    "consulate.synthesis.start | request_id=%s | mode=deadlock | model=%s | "
                    "disagreement=%s | payload_chars=%d",
                    request_id,
                    synthesis_id,
                    agreement.primary_disagreement or "none",
                    len(deadlock_payload),
                )
                logger.debug(
                    "consulate.synthesis.payload | request_id=%s | mode=deadlock | payload=%s",
                    request_id,
                    deadlock_payload[:2000],
                )
                async for event in self._synthesizer.stream_deadlock_summary(
                    prompt,
                    agreement,
                    synthesis_id,
                    analysis_responses,
                ):
                    yield event
                synthesis_ms = int((time.perf_counter() - synthesis_start) * 1000)
                logger.info(
                    "consulate.timing | stage=synthesis | mode=deadlock | synthesis_ms=%d",
                    synthesis_ms,
                )
                logger.info(
                    "consulate.synthesis.complete | mode=deadlock | latency_ms=%d",
                    synthesis_ms,
                )
                _log_session_telemetry(
                    council_ms=council_ms,
                    claims_ms=claims_ms,
                    embeddings_ms=embeddings_ms,
                    similarity_ms=similarity_ms,
                    cluster_ms=cluster_ms,
                    majority_ms=majority_ms,
                    judge_ms=judge_ms,
                    agreement_ms=agreement_ms,
                    synthesis_ms=synthesis_ms,
                    session_start=session_start,
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

        logger.info(
            "consulate.response_count | successful=%d | timed_out=%d | failed=%d | displayed=%d | analysis=%d",
            counts["successful"],
            counts["timed_out"],
            counts["failed"],
            counts["displayed"],
            counts["analysis"],
        )

        yield ConsulateStreamEvent(type="stage", stage="synthesizing")

        fallback_answer = build_consensus_fallback(agreement, analysis_responses)
        synthesis_start = time.perf_counter()
        try:
            consensus_payload, _payload_meta = build_consensus_user_content(
                prompt, analysis_responses, agreement
            )
            logger.info(
                "consulate.synthesis.start | request_id=%s | mode=consensus | model=%s | "
                "inputs=%d | disagreement=%s | payload_chars=%d",
                request_id,
                synthesis_id,
                len(analysis_responses),
                agreement.primary_disagreement or "none",
                len(consensus_payload),
            )
            logger.debug(
                "consulate.synthesis.payload | request_id=%s | mode=consensus | payload=%s",
                request_id,
                consensus_payload[:2000],
            )
            async for event in self._synthesizer.stream_consensus(
                prompt,
                analysis_responses,
                synthesis_id,
                consensus=agreement,
            ):
                yield event
            synthesis_ms = int((time.perf_counter() - synthesis_start) * 1000)
            logger.info(
                "consulate.timing | stage=synthesis | mode=consensus | synthesis_ms=%d",
                synthesis_ms,
            )
            logger.info(
                "consulate.synthesis.complete | mode=consensus | latency_ms=%d",
                synthesis_ms,
            )
            _log_session_telemetry(
                council_ms=council_ms,
                claims_ms=claims_ms,
                embeddings_ms=embeddings_ms,
                similarity_ms=similarity_ms,
                cluster_ms=cluster_ms,
                majority_ms=majority_ms,
                judge_ms=judge_ms,
                agreement_ms=agreement_ms,
                synthesis_ms=synthesis_ms,
                session_start=session_start,
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


def _log_session_telemetry(
    *,
    council_ms: int,
    claims_ms: int,
    embeddings_ms: int,
    similarity_ms: int,
    cluster_ms: int,
    majority_ms: int,
    judge_ms: int,
    agreement_ms: int,
    synthesis_ms: int,
    session_start: float,
) -> None:
    total_ms = int((time.perf_counter() - session_start) * 1000)
    logger.info(
        "consulate.telemetry | council_ms=%d | claims_ms=%d | embeddings_ms=%d | "
        "similarity_ms=%d | cluster_ms=%d | majority_ms=%d | judge_ms=%d | "
        "agreement_ms=%d | synthesis_ms=%d | total_ms=%d",
        council_ms,
        claims_ms,
        embeddings_ms,
        similarity_ms,
        cluster_ms,
        majority_ms,
        judge_ms,
        agreement_ms,
        synthesis_ms,
        total_ms,
    )
