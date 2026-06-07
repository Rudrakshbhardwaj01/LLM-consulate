"""Tests for topic vs recommendation vote support."""

import pytest

from app.orchestrator.consensus.engine import AgreementEngine
from app.schemas.provider import ModelResponse

TOKYO_DOG_PROMPT = "Which is the best dog breed to keep in Tokyo?"

SHIBA = (
    "For a small apartment in Tokyo, I recommend the Shiba Inu. They are compact, "
    "adapt well to apartment living, and are popular in Japan."
)
POODLE = (
    "The Toy Poodle is ideal for Tokyo apartment life — small size, moderate "
    "exercise needs, and well-suited to urban environments."
)
FRENCH_BULLDOG = (
    "Consider a French Bulldog for apartment living in Tokyo. Low space requirements "
    "and manageable exercise make them a strong fit for city dwellers."
)
CAVALIER = (
    "A Cavalier King Charles Spaniel works well in a Tokyo apartment because of its "
    "gentle temperament indoors and moderate size."
)


def _resp(model_id: str, content: str, name: str) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=name,
        role="Analyst",
        content=content,
        success=True,
    )


@pytest.mark.asyncio
async def test_different_breeds_same_topic_do_not_inflate_vote_support():
    engine = AgreementEngine(provider=None, use_llm=False)
    result = await engine.analyze(
        [
            _resp("m1", SHIBA, "GPT-OSS"),
            _resp("m2", POODLE, "MiniMax"),
            _resp("m3", FRENCH_BULLDOG, "Qwen"),
            _resp("m4", CAVALIER, "Nemotron"),
        ],
        TOKYO_DOG_PROMPT,
    )

    assert result.topic_support == pytest.approx(1.0, abs=0.01)
    assert result.recommendation_support == pytest.approx(0.25, abs=0.01)
    assert result.majority_support == pytest.approx(0.25, abs=0.01)
    assert result.majority_support < 1.0
    assert result.is_deadlock is True
    assert result.consensus_outcome == "deadlock"
    assert result.confidence_level == "low"
    assert len(result.supporting_models) == 1


@pytest.mark.asyncio
async def test_two_shiba_increases_recommendation_support():
    engine = AgreementEngine(provider=None, use_llm=False)
    result = await engine.analyze(
        [
            _resp("m1", SHIBA, "GPT-OSS"),
            _resp("m2", SHIBA, "MiniMax"),
            _resp("m3", POODLE, "Qwen"),
            _resp("m4", FRENCH_BULLDOG, "Nemotron"),
        ],
        TOKYO_DOG_PROMPT,
    )

    assert result.topic_support == pytest.approx(1.0, abs=0.01)
    assert result.recommendation_support == pytest.approx(0.5, abs=0.01)
    assert result.majority_support == pytest.approx(0.5, abs=0.01)
    assert result.is_deadlock is False
    assert result.consensus_outcome == "consensus_weak"
