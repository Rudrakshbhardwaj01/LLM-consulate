"""Tests for synthesis prompt compression and message guards."""

from app.orchestrator.consensus.models import ConsensusResult, ExtractedClaims, PositionCluster
from app.orchestrator.synthesis_prompt import (
    build_consensus_user_content,
    build_deadlock_user_content,
    safe_chat_message,
)
from app.schemas.chat import MAX_MESSAGE_CHARS, guard_message_content
from app.schemas.provider import ModelResponse


def _long_text(n: int) -> str:
    return "word " * n


def _resp(model_id: str, content: str, name: str | None = None) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=name or model_id,
        role="Analyst",
        content=content,
        success=True,
    )


def test_guard_message_content_truncates():
    content = "x" * (MAX_MESSAGE_CHARS + 500)
    safe, truncated = guard_message_content(content)
    assert truncated is True
    assert len(safe) <= MAX_MESSAGE_CHARS


def test_safe_chat_message_never_raises():
    msg = safe_chat_message("user", "y" * 20_000)
    assert len(msg.content) <= MAX_MESSAGE_CHARS


def test_consensus_prompt_compresses_large_council():
    responses = [
        _resp(f"m{i}", _long_text(1500), f"Model {i}") for i in range(6)
    ]
    claims = [
        ExtractedClaims(
            modelId=f"m{i}",
            modelName=f"Model {i}",
            positionSummary=f"Position {i}",
            claims=[f"Claim {i}a", f"Claim {i}b"],
            sanitizedText=responses[i].content,
        )
        for i in range(6)
    ]
    consensus = ConsensusResult(
        agreementScore=0.7,
        isDeadlock=False,
        majorityPosition="Majority",
        majoritySupport=0.75,
        extractedClaims=claims,
        clusters=[
            PositionCluster(
                positionKey="a",
                positionLabel="Position A",
                positionSummary="Summary A",
                modelIds=["m0", "m1", "m2"],
                modelNames=["Model 0", "Model 1", "Model 2"],
                count=3,
                support=0.5,
            )
        ],
    )

    user_content, meta = build_consensus_user_content("What is football?", responses, consensus)

    assert len(user_content) <= MAX_MESSAGE_CHARS
    assert meta["compressed"] is True
    assert "Model: Model 0" in user_content or "--- Model 0" in user_content


def test_deadlock_prompt_uses_compact_positions():
    long_majority = _long_text(2000)
    long_minority = _long_text(2000)
    claims = [
        ExtractedClaims(
            modelId="a",
            modelName="Alpha",
            positionSummary="Soccer interpretation",
            claims=["Eleven players", "Goals decide the match"],
            sanitizedText=long_majority,
        ),
        ExtractedClaims(
            modelId="b",
            modelName="Beta",
            positionSummary="American football interpretation",
            claims=["Four downs", "Touchdowns score points"],
            sanitizedText=long_minority,
        ),
    ]
    consensus = ConsensusResult(
        agreementScore=0.32,
        isDeadlock=True,
        majorityPosition=long_majority,
        minorityPosition=long_minority,
        primaryDisagreement="Sport definition",
        majoritySupport=0.25,
        minoritySupport=0.25,
        extractedClaims=claims,
        clusters=[
            PositionCluster(
                positionKey="soccer",
                positionLabel="Soccer",
                positionSummary="Soccer interpretation",
                modelIds=["a"],
                modelNames=["Alpha"],
                count=1,
                support=0.25,
            ),
            PositionCluster(
                positionKey="nfl",
                positionLabel="American Football",
                positionSummary="American football interpretation",
                modelIds=["b"],
                modelNames=["Beta"],
                count=1,
                support=0.25,
            ),
        ],
    )

    user_content, meta = build_deadlock_user_content("Define football", consensus)

    assert len(user_content) <= MAX_MESSAGE_CHARS
    assert long_majority[:200] not in user_content
    assert long_minority[:200] not in user_content
    assert "Model: Alpha" in user_content
    assert "Model: Beta" in user_content
    assert meta["compressed"] is True


def test_deadlock_prompt_scales_to_twenty_models():
    claims = []
    for i in range(20):
        claims.append(
            ExtractedClaims(
                modelId=f"m{i}",
                modelName=f"Model {i}",
                positionSummary=f"Position summary {i}",
                claims=[f"Reason {i}a", f"Reason {i}b"],
                sanitizedText=_long_text(800),
            )
        )
    consensus = ConsensusResult(
        agreementScore=0.2,
        isDeadlock=True,
        majorityPosition=_long_text(1000),
        minorityPosition=_long_text(1000),
        majoritySupport=0.2,
        extractedClaims=claims,
        clusters=[
            PositionCluster(
                positionKey=f"k{i}",
                positionLabel=f"Cluster {i}",
                positionSummary=f"Position summary {i}",
                modelIds=[f"m{i}"],
                modelNames=[f"Model {i}"],
                count=1,
                support=0.05,
            )
            for i in range(20)
        ],
    )

    user_content, _meta = build_deadlock_user_content("Question", consensus)
    assert len(user_content) <= MAX_MESSAGE_CHARS
