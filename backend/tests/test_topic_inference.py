"""Tests for request-scoped topic inference — no cross-topic leakage."""

import pytest

from app.orchestrator.consensus.claim_extractor import (
    _infer_topic,
    extract_claims_heuristic,
    resolve_request_topic,
)
from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.consensus.majority_vote import confidence_label, classify_outcome, ConsensusOutcome
from app.schemas.provider import ModelResponse


@pytest.mark.parametrize(
    "prompt,text",
    [
        (
            "Is Vim better than VS Code?",
            "They compete in different niches. Vim excels at keyboard-driven editing.",
        ),
        (
            "Does Earth orbit the Sun?",
            "Yes. Planets compete for stable orbits through gravitational balance.",
        ),
        (
            "What is AES encryption?",
            "AES is a symmetric encryption standard that competes with ChaCha20.",
        ),
    ],
)
def test_competes_does_not_trigger_pets_topic(prompt: str, text: str):
    assert _infer_topic(prompt, text) == "general"


def test_pet_keywords_still_match():
    assert _infer_topic("Best dog breed for Tokyo?", "") == "pets"
    assert _infer_topic("Best dog breed for Tokyo?", "I recommend a Shiba Inu.") == "pets"


def test_resolve_request_topic_uses_prompt_not_stale_claims():
    claim = extract_claims_heuristic(
        ModelResponse(modelId="m1", modelName="m1", content="They compete often.", success=True),
        "They compete often.",
        "Is Vim better than VS Code?",
    )
    assert resolve_request_topic("Is Vim better than VS Code?", [claim]) == "general"
    assert "pet" not in claim.interpretation.lower()


@pytest.mark.asyncio
async def test_unrelated_question_has_no_pet_disagreement_labels():
    engine = AgreementEngine(provider=None, use_llm=False)
    result = await engine.analyze(
        [
            ModelResponse(
                modelId="a",
                modelName="A",
                content="Vim offers modal editing and excels when you live in the terminal.",
                success=True,
            ),
            ModelResponse(
                modelId="b",
                modelName="B",
                content="VS Code competes through extensions, GUI polish, and IDE features.",
                success=True,
            ),
        ],
        "Vim vs VS Code — which is better?",
    )

    if result.disagreement:
        combined = (
            f"{result.disagreement.disputed_concept} "
            f"{result.disagreement.majority_position} "
            f"{result.disagreement.minority_position}"
        ).lower()
        assert "pet" not in combined


def test_outcome_and_confidence_align_with_vote_support():
    assert classify_outcome(0.40, False) == ConsensusOutcome.DEADLOCK
    assert confidence_label(0.40) == "low"
    assert classify_outcome(0.80, False) == ConsensusOutcome.CONSENSUS_STRONG
    assert confidence_label(0.80) == "high"
