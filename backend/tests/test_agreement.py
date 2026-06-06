"""Unit tests for council agreement analysis (legacy scenarios)."""

import pytest

from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.content_sanitizer import sanitize_council_content
from app.orchestrator.similarity import compute_similarity
from app.schemas.provider import ModelResponse


def _response(model_id: str, content: str, reasoning: str | None = None) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=model_id,
        role="Analyst",
        content=content,
        reasoning=reasoning,
        success=True,
    )


FOOTBALL_A = (
    "Football is a globally popular sport played between two teams of eleven players. "
    "The objective is to score goals by getting the ball into the opposing team's net. "
    "Major competitions include the FIFA World Cup and UEFA Champions League. "
    "Success requires skill, strategy, and teamwork."
)

FOOTBALL_B = (
    "Soccer, known as football outside North America, is a team sport where two squads "
    "of 11 players compete to score. It is the world's most watched sport, with the "
    "World Cup as its premier tournament. Players need athletic skill and tactical planning."
)

FOOTBALL_C = (
    "Football is one of the world's most beloved sports. Two teams of eleven players "
    "vie to score goals using skill and strategy. The sport enjoys massive global "
    "popularity and features major events like the World Cup and Champions League."
)


@pytest.fixture
def engine() -> AgreementEngine:
    return AgreementEngine(provider=None, use_llm=False)


@pytest.mark.asyncio
async def test_football_responses_score_high_agreement(engine: AgreementEngine):
    result = await engine.analyze(
        [
            _response("model-a", FOOTBALL_A),
            _response("model-b", FOOTBALL_B),
            _response("model-c", FOOTBALL_C),
        ],
        prompt="Write a note on football",
    )
    assert result.agreement_score >= 0.65
    assert result.is_deadlock is False
    assert result.majority_support >= 0.65


@pytest.mark.asyncio
async def test_reasoning_does_not_affect_agreement(engine: AgreementEngine):
    reasoning_a = (
        "The user asks for a short note on football. We need to cover basics: "
        "teams, scoring, popularity, and major tournaments. Let me draft a concise answer."
    )
    reasoning_b = (
        "The user wants a brief football note. I should mention it is a sport with "
        "two teams, goals, and global appeal. I'll write a short paragraph."
    )
    result = await engine.analyze(
        [
            _response("model-a", FOOTBALL_A, reasoning=reasoning_a),
            _response("model-b", FOOTBALL_B, reasoning=reasoning_b),
        ],
        prompt="Write a note on football",
    )
    assert result.agreement_score >= 0.65
    assert result.is_deadlock is False


def test_embedded_planning_stripped_from_content():
    polluted = (
        "The user asks for a short note on football.\n\n"
        "We need to write something concise.\n\n"
        f"{FOOTBALL_A}"
    )
    sanitized = sanitize_council_content(polluted)
    assert "user asks" not in sanitized.lower()
    assert "football is a globally popular sport" in sanitized.lower()


@pytest.mark.asyncio
async def test_genuine_disagreement_triggers_deadlock(engine: AgreementEngine):
    invest_a = (
        "Invest aggressively in growth stocks and cryptocurrency. High risk yields "
        "the best long-term returns for young investors willing to accept volatility."
    )
    invest_b = (
        "Conservative investors should prioritize bonds, index funds, and cash reserves. "
        "Capital preservation matters more than chasing speculative high-risk assets."
    )
    result = await engine.analyze(
        [_response("bull", invest_a), _response("bear", invest_b)],
        prompt="How should I invest?",
    )
    assert result.is_deadlock is True
    assert result.primary_disagreement != ""


def test_semantic_similarity_on_football_paraphrases():
    sim = compute_similarity(FOOTBALL_A, FOOTBALL_B)
    assert sim >= 0.65
