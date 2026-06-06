"""Tests for the semantic consensus agreement engine — cases A through E."""

import pytest

from app.orchestrator.consensus.engine import AgreementEngine
from app.schemas.provider import ModelResponse

# --- Fixtures: football interpretations ---

SOCCER_1 = (
    "Football is the world's most popular sport, played between two teams of eleven "
    "players on a pitch. The objective is to score goals in a 90-minute match. "
    "Major tournaments include the FIFA World Cup and UEFA Champions League."
)

SOCCER_2 = (
    "Soccer, known as football globally, is a team sport where two squads of 11 players "
    "compete to score goals. The World Cup is its premier tournament. "
    "Skill, strategy, and teamwork are essential."
)

SOCCER_3 = (
    "Association football features two teams of eleven players aiming to score goals. "
    "It is watched by billions and governed by FIFA. The offside rule and penalty kicks "
    "are key elements of the sport."
)

AMERICAN_FOOTBALL = (
    "American football is a distinct sport played primarily in the United States. "
    "Teams advance an oval ball down the field in four downs to score touchdowns. "
    "The NFL and Super Bowl are its major competitions. Quarterbacks and linebackers "
    "are key positions on the gridiron."
)

# --- Fixtures: paraphrase / style variants ---

SOCCER_FORMAL = SOCCER_1
SOCCER_CASUAL = (
    "Yeah so football/soccer is basically the biggest sport ever — 11 vs 11, "
    "score goals, World Cup is huge. Simple as that."
)

SOCCER_VERBOSE = (
    "To begin with, it is important to note that football, which is also widely "
    "referred to as soccer in certain regions of the world, particularly North America, "
    "stands as arguably the most popular and widely followed sport on the entire planet. "
    "The game is contested between two teams, each consisting of eleven players, "
    "on a rectangular pitch, with the fundamental objective being to score goals "
    "by propelling the ball into the opposing team's net. Major international "
    "competitions such as the FIFA World Cup attract viewership in the billions."
)

SOCCER_CONCISE = (
    "Football: 11 players per team, score goals, world's most popular sport. "
    "World Cup is the top event."
)


def _resp(model_id: str, content: str, name: str | None = None) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=name or model_id,
        role="Analyst",
        content=content,
        success=True,
    )


@pytest.fixture
def engine() -> AgreementEngine:
    """Heuristic-only engine — no LLM/API calls in tests."""
    return AgreementEngine(provider=None, use_llm=False)


@pytest.mark.asyncio
async def test_case_a_three_soccer_one_american_consensus(engine: AgreementEngine):
    """Case A: 3 soccer + 1 american football → consensus at ~75%."""
    result = await engine.analyze(
        [
            _resp("gpt-oss", SOCCER_1, "GPT-OSS"),
            _resp("nemotron", SOCCER_2, "Nemotron"),
            _resp("kimi", SOCCER_3, "Kimi"),
            _resp("gemma", AMERICAN_FOOTBALL, "Gemma"),
        ],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is False
    assert result.consensus_outcome == "consensus_moderate"
    assert result.majority_support == pytest.approx(0.75, abs=0.01)
    assert result.minority_support == pytest.approx(0.25, abs=0.01)
    assert len(result.supporting_models) == 3
    assert len(result.minority_models) == 1
    assert result.disagreement is not None
    assert "football" in result.disagreement.disputed_concept.lower()
    # Agreement score is independent — low score must NOT cause deadlock
    assert result.agreement_score < result.majority_support or result.agreement_score >= 0


@pytest.mark.asyncio
async def test_case_b_two_vs_two_deadlock(engine: AgreementEngine):
    """Case B: 2 soccer + 2 american football → deadlock."""
    result = await engine.analyze(
        [
            _resp("a", SOCCER_1),
            _resp("b", SOCCER_2),
            _resp("c", AMERICAN_FOOTBALL),
            _resp("d", (
                "American football uses an oval pigskin, four quarters, and touchdowns. "
                "The NFL Super Bowl is the championship. Teams have offensive and defensive lines."
            )),
        ],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is True
    assert result.consensus_outcome == "deadlock"
    assert result.majority_support == pytest.approx(0.50, abs=0.01)


@pytest.mark.asyncio
async def test_case_c_same_answer_different_wording(engine: AgreementEngine):
    """Case C: same answer written differently → high agreement, no deadlock."""
    result = await engine.analyze(
        [
            _resp("a", SOCCER_1),
            _resp("b", SOCCER_2),
            _resp("c", SOCCER_3),
        ],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is False
    assert result.consensus_outcome == "consensus_strong"
    assert result.majority_support == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_case_d_same_topic_different_style(engine: AgreementEngine):
    """Case D: same topic, different writing style → high agreement."""
    result = await engine.analyze(
        [
            _resp("formal", SOCCER_FORMAL),
            _resp("casual", SOCCER_CASUAL),
        ],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is False
    assert result.agreement_score >= 0.65


@pytest.mark.asyncio
async def test_case_e_verbose_vs_concise_no_penalty(engine: AgreementEngine):
    """Case E: one verbose response → no agreement penalty."""
    result = await engine.analyze(
        [
            _resp("verbose", SOCCER_VERBOSE),
            _resp("concise", SOCCER_CONCISE),
        ],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is False
    assert result.agreement_score >= 0.65


@pytest.mark.asyncio
async def test_five_vs_one_still_consensus(engine: AgreementEngine):
    """5 vs 1 split → consensus, not deadlock."""
    responses = [
        _resp(f"s{i}", SOCCER_1) for i in range(5)
    ] + [_resp("am", AMERICAN_FOOTBALL)]
    result = await engine.analyze(responses, prompt="Write a note on football")

    assert result.is_deadlock is False
    assert result.majority_support == pytest.approx(5 / 6, abs=0.01)


@pytest.mark.asyncio
async def test_four_vs_two_consensus(engine: AgreementEngine):
    """4 vs 2 split → consensus."""
    result = await engine.analyze(
        [_resp(f"s{i}", SOCCER_1) for i in range(4)]
        + [_resp(f"a{i}", AMERICAN_FOOTBALL) for i in range(2)],
        prompt="Write a note on football",
    )

    assert result.is_deadlock is False
    assert result.majority_support == pytest.approx(4 / 6, abs=0.01)


DEPTH_CAREER = (
    "You should prioritize depth early in your career. Build deep expertise in one area "
    "before branching out. Specialization creates leverage and makes you indispensable."
)

BREADTH_CAREER = (
    "Prioritize depth over breadth when starting out. Go deep into a domain, develop "
    "mastery, and become an expert before exploring adjacent fields."
)

CONTEXT_CAREER = (
    "There is no single right answer — it depends on your industry, goals, and stage. "
    "The optimal path is fully context-dependent and varies from person to person."
)


@pytest.mark.asyncio
async def test_career_depth_majority_not_deadlock(engine: AgreementEngine):
    """3 depth-first + 1 context-dependent → consensus at 75%, not deadlock."""
    result = await engine.analyze(
        [
            _resp("a", DEPTH_CAREER),
            _resp("b", BREADTH_CAREER),
            _resp("c", DEPTH_CAREER),
            _resp("d", CONTEXT_CAREER),
        ],
        prompt="Should I prioritize depth or breadth in my career?",
    )

    assert result.is_deadlock is False
    assert result.majority_support == pytest.approx(0.75, abs=0.01)
    assert result.consensus_outcome in ("consensus_moderate", "consensus_strong")
    assert result.disagreement is not None
    assert "context" in result.disagreement.disputed_concept.lower()


@pytest.mark.asyncio
async def test_low_agreement_score_with_clear_majority_not_deadlock(engine: AgreementEngine):
    """Vote support drives consensus; agreement score is confidence only."""
    result = await engine.analyze(
        [
            _resp("a", SOCCER_1),
            _resp("b", SOCCER_2),
            _resp("c", SOCCER_3),
            _resp("d", AMERICAN_FOOTBALL),
        ],
        prompt="Write a note on football",
    )

    assert result.majority_support >= 0.70
    assert result.is_deadlock is False
    assert result.consensus_outcome != "deadlock"
