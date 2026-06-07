"""Semantic consensus pipeline orchestrator."""

import asyncio
import time

from app.orchestrator.consensus.claim_extractor import extract_all_claims, resolve_request_topic
from app.orchestrator.consensus.embeddings import compute_embedding_similarity
from app.orchestrator.consensus.judge import run_judge
from app.orchestrator.consensus.majority_vote import (
    ConsensusOutcome,
    analyze_majority,
    analyze_recommendation_vote,
    classify_outcome,
    confidence_label,
    outcome_display_label,
)
from app.orchestrator.consensus.models import AgreementTiming, ConsensusResult
from app.orchestrator.consensus.position_clusterer import cluster_positions
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.consulate import MinorityReport
from app.schemas.provider import ModelResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Agreement score = linguistic alignment. Outcome/confidence follow vote support.
WEIGHT_JUDGE = 0.60
WEIGHT_EMBEDDING = 0.40


class AgreementEngine:
    """Semantic consensus pipeline — deadlock is vote-driven, never score-driven."""

    def __init__(
        self,
        provider: NvidiaProvider | None = None,
        judge_model_id: str = "gpt-oss-120b",
        embedding_model_id: str = "nvidia/nv-embedqa-e5-v5",
        use_llm: bool = False,
        use_llm_claims: bool | None = None,
        use_llm_judge: bool | None = None,
        use_embeddings_api: bool = False,
    ) -> None:
        self._provider = provider
        self._judge_model_id = judge_model_id
        self._embedding_model_id = embedding_model_id
        self._use_llm_claims = use_llm_claims if use_llm_claims is not None else use_llm
        self._use_llm_judge = use_llm_judge if use_llm_judge is not None else use_llm
        self._use_embeddings_api = use_embeddings_api

    async def analyze(
        self,
        responses: list[ModelResponse],
        prompt: str,
        request_id: str = "",
    ) -> ConsensusResult:
        rid = request_id or "n/a"
        agreement_start = time.perf_counter()
        successful = [r for r in responses if r.success and r.effective_content]

        if len(successful) < 2:
            only = successful[0].effective_content if successful else ""
            return ConsensusResult(
                agreement_score=1.0,
                is_deadlock=False,
                consensus_outcome=ConsensusOutcome.CONSENSUS_STRONG.value,
                outcome_label=outcome_display_label(ConsensusOutcome.CONSENSUS_STRONG),
                confidence_level="high",
                majority_position=only,
                majority_support=1.0,
            )

        logger.info(
            "consulate.agreement.config | request_id=%s | use_llm_claims=%s | "
            "use_llm_judge=%s | use_embeddings_api=%s",
            rid,
            self._use_llm_claims,
            self._use_llm_judge,
            self._use_embeddings_api,
        )

        claims_start = time.perf_counter()
        claims = await extract_all_claims(
            self._provider,
            self._judge_model_id,
            successful,
            prompt,
            use_llm=self._use_llm_claims,
            request_id=request_id,
        )
        claims_ms = int((time.perf_counter() - claims_start) * 1000)

        cluster_start = time.perf_counter()
        clusters, cluster_timing = cluster_positions(claims, request_id=request_id)
        cluster_wall_ms = int((time.perf_counter() - cluster_start) * 1000)
        cluster_ms = max(0, cluster_wall_ms - cluster_timing.similarity_ms)
        similarity_ms = cluster_timing.similarity_ms
        topic = resolve_request_topic(prompt, claims)

        majority_start = time.perf_counter()
        (
            majority,
            minority,
            topic_support,
            _topic_minority_support,
            _topic_deadlock,
            _topic_outcome,
            disagreement,
        ) = analyze_majority(
            clusters, prompt=prompt, topic=topic, request_id=request_id
        )
        majority_ms = int((time.perf_counter() - majority_start) * 1000)

        (
            vote_support,
            vote_minority_support,
            _top_recommendation,
            rec_supporting_models,
            rec_minority_models,
            vote_deadlock,
        ) = analyze_recommendation_vote(claims)

        is_deadlock = vote_deadlock
        outcome = classify_outcome(vote_support, is_deadlock)

        logger.info(
            "consulate.vote_support | request_id=%s | topic_support=%.0f%% | "
            "vote_support=%.0f%% | outcome=%s | deadlock=%s",
            rid,
            topic_support * 100,
            vote_support * 100,
            outcome.value,
            is_deadlock,
        )

        texts = [c.sanitized_text for c in claims]
        need_judge_llm = self._use_llm_judge and is_deadlock

        embeddings_start = time.perf_counter()
        if need_judge_llm and self._use_embeddings_api:
            embedding_sim, embeddings_inner_ms = await compute_embedding_similarity(
                self._provider, texts, self._embedding_model_id, use_api=True, request_id=request_id
            )
        else:
            embedding_sim, embeddings_inner_ms = await compute_embedding_similarity(
                self._provider, texts, self._embedding_model_id, use_api=False, request_id=request_id
            )
        embeddings_ms = int((time.perf_counter() - embeddings_start) * 1000)
        if embeddings_inner_ms > embeddings_ms:
            embeddings_ms = embeddings_inner_ms

        judge_start = time.perf_counter()
        if need_judge_llm:
            verdict = await run_judge(
                self._provider,
                self._judge_model_id,
                prompt,
                claims,
                clusters,
                use_llm=True,
                disagreement=disagreement,
                majority=majority,
                minority=minority,
                majority_support=vote_support,
                is_deadlock=is_deadlock,
                request_id=request_id,
            )
        else:
            verdict = await run_judge(
                self._provider,
                self._judge_model_id,
                prompt,
                claims,
                clusters,
                use_llm=False,
                disagreement=disagreement,
                majority=majority,
                minority=minority,
                majority_support=vote_support,
                is_deadlock=is_deadlock,
                request_id=request_id,
            )
        judge_ms = int((time.perf_counter() - judge_start) * 1000)

        judge_align = (
            verdict.confidence if verdict.fundamentally_agree else (1.0 - verdict.confidence) * 0.5
        )
        agreement_score = round(
            min(1.0, max(0.0, WEIGHT_JUDGE * judge_align + WEIGHT_EMBEDDING * embedding_sim)),
            3,
        )
        # Confidence tracks vote support — the metric shown as "Vote Support" in the UI.
        conf_level = confidence_label(vote_support)

        minority_reports: list[MinorityReport] = []
        if majority:
            majority_ids = set(majority.model_ids)
            for c in claims:
                if c.model_id not in majority_ids:
                    minority_reports.append(
                        MinorityReport(
                            model=c.model_name,
                            modelId=c.model_id,
                            role="",
                            response=c.sanitized_text,
                            reasoning=None,
                        )
                    )

        primary_disagreement = disagreement.disputed_concept if disagreement else ""
        agreement_ms = int((time.perf_counter() - agreement_start) * 1000)

        timing = AgreementTiming(
            claims_ms=claims_ms,
            embeddings_ms=embeddings_ms,
            similarity_ms=similarity_ms,
            cluster_ms=cluster_ms,
            cluster_merge_ms=cluster_timing.merge_ms,
            majority_ms=majority_ms,
            judge_ms=judge_ms,
            agreement_ms=agreement_ms,
        )

        logger.info(
            "consulate.consensus.result | request_id=%s | outcome=%s | vote_support=%.0f%% | "
            "topic_support=%.0f%% | agreement_score=%.3f | confidence=%s | deadlock=%s | "
            "claims_ms=%d | embeddings_ms=%d | similarity_ms=%d | cluster_ms=%d | "
            "majority_ms=%d | judge_ms=%d | agreement_ms=%d",
            rid,
            outcome.value,
            vote_support * 100,
            topic_support * 100,
            agreement_score,
            conf_level,
            is_deadlock,
            claims_ms,
            embeddings_ms,
            similarity_ms,
            cluster_ms,
            majority_ms,
            judge_ms,
            agreement_ms,
        )
        if disagreement:
            logger.info(
                "consulate.disagreement | request_id=%s | reason=%s",
                rid,
                disagreement.disputed_concept,
            )

        return ConsensusResult(
            agreement_score=agreement_score,
            is_deadlock=is_deadlock,
            consensus_outcome=outcome.value,
            outcome_label=outcome_display_label(outcome),
            confidence_level=conf_level,
            majority_position=_cluster_representative_text(majority, claims),
            minority_position=_cluster_representative_text(minority, claims) if minority else "",
            primary_disagreement=primary_disagreement,
            majority_support=round(vote_support, 3),
            minority_support=round(vote_minority_support, 3),
            topic_support=round(topic_support, 3),
            recommendation_support=round(vote_support, 3),
            supporting_models=rec_supporting_models,
            minority_models=rec_minority_models,
            disagreement=disagreement,
            extracted_claims=claims,
            clusters=clusters,
            judge_verdict=verdict,
            embedding_similarity=round(embedding_sim, 3),
            majority_vote_component=round(vote_support, 3),
            judge_component=round(judge_align, 3),
            embedding_component=round(embedding_sim, 3),
            minority_reports=minority_reports,
            timing=timing,
        )


def _cluster_representative_text(cluster, claims: list) -> str:
    if not cluster:
        return ""
    claims_by_id = {c.model_id: c for c in claims}
    for mid in cluster.model_ids:
        c = claims_by_id.get(mid)
        if c and c.sanitized_text:
            return c.sanitized_text
    return cluster.position_summary
