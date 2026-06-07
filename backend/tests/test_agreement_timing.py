"""Tests for trustworthy agreement-analysis timing boundaries."""

import time

import pytest

from app.orchestrator.consensus.engine import AgreementEngine
from app.schemas.provider import ModelResponse


def _large_response(model_id: str, size: int) -> ModelResponse:
    paragraph = (
        "For Tokyo apartment living, the Shiba Inu is an excellent compact breed. "
        "They adapt well indoors with daily walks. "
    )
    content = paragraph * (size // len(paragraph) + 1)
    content = content[:size]
    return ModelResponse(
        modelId=model_id,
        modelName=model_id,
        role="Analyst",
        content=content,
        success=True,
    )


@pytest.mark.asyncio
async def test_heuristic_judge_ms_is_milliseconds_not_embedding_cost():
    engine = AgreementEngine(provider=None, use_llm=False)
    responses = [_large_response(f"m{i}", 9000) for i in range(5)]

    result = await engine.analyze(responses, "Which is the best dog breed to keep in Tokyo?")

    assert result.timing is not None
    assert result.timing.judge_ms < 100
    assert result.judge_verdict is not None
    assert result.judge_verdict.source == "heuristic"


@pytest.mark.asyncio
async def test_large_council_responses_complete_agreement_under_two_seconds():
    engine = AgreementEngine(provider=None, use_llm=False)
    responses = [_large_response(f"m{i}", 9000) for i in range(5)]

    start = time.perf_counter()
    result = await engine.analyze(responses, "Which is the best dog breed to keep in Tokyo?")
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    timing = result.timing
    assert timing is not None
    assert timing.claims_ms < 100
    assert timing.cluster_ms < 500
    assert timing.similarity_ms < 500
    assert timing.majority_ms < 100
    assert timing.judge_ms < 100
    assert timing.embeddings_ms < 500
    assert timing.agreement_ms < 2000
    assert elapsed_ms < 2000


@pytest.mark.asyncio
async def test_embeddings_ms_separate_from_judge_ms():
    engine = AgreementEngine(provider=None, use_llm=False)
    responses = [_large_response(f"m{i}", 8000) for i in range(5)]

    result = await engine.analyze(responses, "Write a note on football")

    timing = result.timing
    assert timing is not None
    assert timing.embeddings_ms >= 0
    assert timing.judge_ms < 100
    assert timing.agreement_ms >= timing.judge_ms
