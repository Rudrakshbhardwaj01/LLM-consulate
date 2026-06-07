"""Tests for semantic position clustering."""

import pytest

from app.orchestrator.consensus.claim_extractor import extract_claims_heuristic
from app.orchestrator.consensus.engine import AgreementEngine
from app.orchestrator.consensus.majority_vote import analyze_majority
from app.orchestrator.consensus.position_clusterer import cluster_positions
from app.schemas.provider import ModelResponse

TOKYO_DOG_PROMPT = "Which is the best dog breed to keep in Tokyo?"

SHIBA = (
    "For a small apartment in Tokyo, I recommend the Shiba Inu. They are compact, "
    "adapt well to apartment living, and are popular in Japan."
)
FRENCH_BULLDOG = (
    "The French Bulldog is ideal for Tokyo apartment life — small size, moderate "
    "exercise needs, and well-suited to urban environments."
)
POMERANIAN = (
    "Consider a Pomeranian for apartment living in Tokyo. Low space requirements "
    "and manageable exercise make them a strong fit for city dwellers."
)
SHIH_TZU = (
    "A Shih Tzu works well in a Tokyo apartment because of its small stature, calm "
    "temperament indoors, and low space needs."
)
MALTESE = (
    "Maltese dogs are apartment-friendly and suited to compact urban homes in Tokyo "
    "when owners want a small, adaptable companion."
)
HUSKY = (
    "If you have access to substantial outdoor exercise, a Siberian Husky can work, "
    "but it is not ideal for small Tokyo apartments due to high energy and space needs."
)


def _resp(model_id: str, content: str, name: str) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=name,
        role="Analyst",
        content=content,
        success=True,
    )


def _claims_for(*responses: ModelResponse):
    return [
        extract_claims_heuristic(resp, resp.content, TOKYO_DOG_PROMPT)
        for resp in responses
    ]


def test_dog_recommendations_cluster_by_shared_conclusion():
    responses = [
        _resp("m1", SHIBA, "GPT-OSS"),
        _resp("m2", FRENCH_BULLDOG, "MiniMax"),
        _resp("m3", POMERANIAN, "Qwen"),
        _resp("m4", SHIH_TZU, "Nemotron"),
        _resp("m5", MALTESE, "Kimi"),
        _resp("m6", HUSKY, "Gemma"),
    ]
    claims = _claims_for(*responses)
    clusters, _timing = cluster_positions(claims)

    assert len(clusters) == 2
    assert clusters[0].count == 5
    assert clusters[0].support >= 0.83
    assert clusters[1].count == 1


def test_dog_recommendations_reach_majority_not_deadlock():
    responses = [
        _resp("m1", SHIBA, "GPT-OSS"),
        _resp("m2", FRENCH_BULLDOG, "MiniMax"),
        _resp("m3", POMERANIAN, "Qwen"),
        _resp("m4", SHIH_TZU, "Nemotron"),
        _resp("m5", MALTESE, "Kimi"),
        _resp("m6", HUSKY, "Gemma"),
    ]
    claims = _claims_for(*responses)
    clusters, _timing = cluster_positions(claims)
    majority, _minority, maj_support, _min_support, is_deadlock, outcome, _ = analyze_majority(
        clusters,
        prompt=TOKYO_DOG_PROMPT,
        topic="pets",
    )

    assert is_deadlock is False
    assert maj_support >= 0.80
    assert outcome.value.startswith("consensus")


def test_dog_topic_support_high_but_recommendation_support_lower():
    responses = [
        _resp("m1", SHIBA, "GPT-OSS"),
        _resp("m2", FRENCH_BULLDOG, "MiniMax"),
        _resp("m3", POMERANIAN, "Qwen"),
        _resp("m4", SHIH_TZU, "Nemotron"),
        _resp("m5", MALTESE, "Kimi"),
    ]
    claims = _claims_for(*responses)
    clusters, _timing = cluster_positions(claims)
    majority, _minority, topic_support, _min_support, is_deadlock, outcome, _ = analyze_majority(
        clusters,
        prompt=TOKYO_DOG_PROMPT,
        topic="pets",
    )

    assert is_deadlock is False
    assert topic_support >= 0.80
    assert outcome.value.startswith("consensus")


@pytest.mark.asyncio
async def test_dog_recommendations_engine_finds_consensus():
    engine = AgreementEngine(provider=None, use_llm=False)
    result = await engine.analyze(
        [
            _resp("m1", SHIBA, "GPT-OSS"),
            _resp("m2", FRENCH_BULLDOG, "MiniMax"),
            _resp("m3", POMERANIAN, "Qwen"),
            _resp("m4", SHIH_TZU, "Nemotron"),
            _resp("m5", MALTESE, "Kimi"),
            _resp("m6", HUSKY, "Gemma"),
        ],
        TOKYO_DOG_PROMPT,
    )

    assert result.is_deadlock is True
    assert result.topic_support >= 0.80
    assert result.recommendation_support < 1.0
    assert result.consensus_outcome == "deadlock"


@pytest.mark.parametrize(
    ("content", "expected_key"),
    [
        (
            "For Tokyo apartment living, the Shiba Inu is an excellent choice. Compact size, "
            "adapts well indoors, though they enjoy daily walks.",
            "apartment_friendly_pet",
        ),
        (
            "The Shiba Inu is not suited to sedentary owners but works well in Tokyo apartments "
            "with daily walks.",
            "apartment_friendly_pet",
        ),
        (
            "While not ideal for tiny apartments, the Shiba Inu remains the best Tokyo choice "
            "for active urban owners.",
            "apartment_friendly_pet",
        ),
        (
            "I recommend the Toy Poodle for Tokyo apartments. Small, intelligent, low shedding, "
            "and well-suited to urban life.",
            "apartment_friendly_pet",
        ),
        (
            "For Tokyo living, the Toy Poodle is excellent. Not ideal if you want a guard dog, "
            "but perfect for apartments.",
            "apartment_friendly_pet",
        ),
        (
            "The French Bulldog is ideal for apartment life in Tokyo — moderate exercise, quiet, "
            "and compact.",
            "apartment_friendly_pet",
        ),
        (
            "French Bulldogs are not suited to extreme heat but are ideal for Tokyo apartment life.",
            "apartment_friendly_pet",
        ),
        (
            "A Cavalier King Charles Spaniel fits Tokyo apartment living well due to its gentle "
            "temperament and moderate size.",
            "apartment_friendly_pet",
        ),
        (
            "A Siberian Husky is not ideal for small Tokyo apartments due to high energy and "
            "space needs.",
            "active_pet",
        ),
    ],
)
def test_tokyo_dog_breed_classification(content: str, expected_key: str):
    claims = extract_claims_heuristic(
        _resp("m1", content, "Model"),
        content,
        TOKYO_DOG_PROMPT,
    )
    assert claims.position_key == expected_key


def test_tokyo_apartment_breeds_form_majority_cluster():
    responses = [
        _resp(
            "m1",
            "The Shiba Inu is not suited to sedentary owners but works well in Tokyo apartments.",
            "GPT-OSS",
        ),
        _resp(
            "m2",
            "For Tokyo living, the Toy Poodle is excellent and perfect for apartments.",
            "MiniMax",
        ),
        _resp(
            "m3",
            "French Bulldogs are not suited to extreme heat but are ideal for Tokyo apartment life.",
            "Qwen",
        ),
        _resp(
            "m4",
            "A Cavalier King Charles Spaniel fits Tokyo apartment living well indoors.",
            "Nemotron",
        ),
        _resp(
            "m5",
            "A Siberian Husky is not ideal for small Tokyo apartments due to high energy.",
            "Gemma",
        ),
    ]
    claims = _claims_for(*responses)
    clusters, _timing = cluster_positions(claims)

    assert clusters[0].position_key == "apartment_friendly_pet"
    assert clusters[0].count == 4
    assert clusters[1].position_key == "active_pet"
