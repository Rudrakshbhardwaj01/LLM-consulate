"""Semantic consensus pipeline orchestrator."""

import asyncio
import time

from app.orchestrator.consensus.claim_extractor import extract_all_claims
from app.orchestrator.consensus.embeddings import compute_embedding_similarity
from app.orchestrator.consensus.judge import run_judge
from app.orchestrator.consensus.majority_vote import (
    ConsensusOutcome,
    analyze_majority,
    confidence_label,
    outcome_display_label,
)
from app.orchestrator.consensus.models import ConsensusResult
from app.orchestrator.consensus.position_clusterer import cluster_positions
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.consulate import MinorityReport
from app.schemas.provider import ModelResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Agreement score = linguistic alignment (confidence only). Vote support is separate.
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
    ) -> ConsensusResult:
        start = time.perf_counter()
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

        claims_start = time.perf_counter()
        claims = await extract_all_claims(
            self._provider,
            self._judge_model_id,
            successful,
            prompt,
            use_llm=self._use_llm_claims,
        )
        claims_ms = int((time.perf_counter() - claims_start) * 1000)

        cluster_start = time.perf_counter()
        clusters = cluster_positions(claims)
        cluster_ms = int((time.perf_counter() - cluster_start) * 1000)
        topic = claims[0].topic if claims else "general"

        # Primary: majority vote determines consensus vs deadlock
        (
            majority,
            minority,
            maj_support,
            min_support,
            is_deadlock,
            outcome,
            disagreement,
        ) = analyze_majority(clusters, prompt=prompt, topic=topic)

        texts = [c.sanitized_text for c in claims]
        need_judge_llm = self._use_llm_judge and is_deadlock

        judge_start = time.perf_counter()
        if need_judge_llm and self._use_embeddings_api:
            embedding_sim, verdict = await asyncio.gather(
                compute_embedding_similarity(
                    self._provider, texts, self._embedding_model_id, use_api=True
                ),
                run_judge(
                    self._provider, self._judge_model_id, prompt, claims, clusters, use_llm=True
                ),
            )
        elif need_judge_llm:
            embedding_sim = await compute_embedding_similarity(
                self._provider, texts, self._embedding_model_id, use_api=False
            )
            verdict = await run_judge(
                self._provider, self._judge_model_id, prompt, claims, clusters, use_llm=True
            )
        else:
            embedding_sim = await compute_embedding_similarity(
                self._provider, texts, self._embedding_model_id, use_api=False
            )
            verdict = await run_judge(
                self._provider, self._judge_model_id, prompt, claims, clusters, use_llm=False
            )
        judge_ms = int((time.perf_counter() - judge_start) * 1000)

        # Agreement score = confidence in linguistic alignment (never triggers deadlock)
        judge_align = (
            verdict.confidence if verdict.fundamentally_agree else (1.0 - verdict.confidence) * 0.5
        )
        agreement_score = round(
            min(1.0, max(0.0, WEIGHT_JUDGE * judge_align + WEIGHT_EMBEDDING * embedding_sim)),
            3,
        )
        conf_level = confidence_label(agreement_score)

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

        logger.info(
            "consulate.consensus.result | outcome=%s | vote_support=%.0f%% | "
            "agreement_score=%.3f | confidence=%s | deadlock=%s | "
            "claims_ms=%d | cluster_ms=%d | judge_ms=%d | total_ms=%d",
            outcome.value,
            maj_support * 100,
            agreement_score,
            conf_level,
            is_deadlock,
            claims_ms,
            cluster_ms,
            judge_ms,
            int((time.perf_counter() - start) * 1000),
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
            majority_support=round(maj_support, 3),
            minority_support=round(min_support, 3),
            supporting_models=majority.model_names if majority else [],
            minority_models=minority.model_names if minority else [],
            disagreement=disagreement,
            extracted_claims=claims,
            clusters=clusters,
            judge_verdict=verdict,
            embedding_similarity=round(embedding_sim, 3),
            majority_vote_component=round(maj_support, 3),
            judge_component=round(judge_align, 3),
            embedding_component=round(embedding_sim, 3),
            minority_reports=minority_reports,
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
