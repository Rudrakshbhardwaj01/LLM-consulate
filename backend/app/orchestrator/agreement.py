"""Backwards-compatible agreement entry point — delegates to semantic consensus engine."""

from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.consensus.models import ConsensusResult
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.provider import ModelResponse

# Re-export legacy dataclass shape for any remaining imports
AgreementResult = ConsensusResult


async def analyze_agreement(
    responses: list[ModelResponse],
    prompt: str = "",
    provider: NvidiaProvider | None = None,
    judge_model_id: str = "gpt-oss-120b",
    embedding_model_id: str = "nvidia/nv-embedqa-e5-v5",
    use_llm: bool = False,
    threshold: float = 0.60,  # noqa: ARG001 — kept for backwards compatibility
) -> ConsensusResult:
    """Analyze council agreement using the semantic consensus pipeline."""
    engine = AgreementEngine(
        provider=provider,
        judge_model_id=judge_model_id,
        embedding_model_id=embedding_model_id,
        use_llm=use_llm,
    )
    return await engine.analyze(responses, prompt)
