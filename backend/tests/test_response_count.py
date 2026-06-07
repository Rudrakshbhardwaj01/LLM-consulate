"""Tests for council response counting consistency."""

from app.orchestrator.consulate import _count_council_responses, _has_displayable_response
from app.schemas.provider import ModelResponse


def _resp(
    model_id: str,
    *,
    success: bool = True,
    content: str = "answer",
    error: str | None = None,
) -> ModelResponse:
    return ModelResponse(
        modelId=model_id,
        modelName=model_id,
        role="Analyst",
        content=content,
        success=success,
        error=error,
    )


def test_five_successful_responses_count_as_five():
    results = [_resp(f"m{i}") for i in range(5)]
    counts = _count_council_responses(results)

    assert counts["successful"] == 5
    assert counts["displayed"] == 5
    assert counts["analysis"] == 5


def test_four_success_one_timeout():
    results = [
        _resp("m1"),
        _resp("m2"),
        _resp("m3"),
        _resp("m4"),
        _resp("m5", success=False, content="", error="Timed out after 45s"),
    ]
    counts = _count_council_responses(results)

    assert counts["successful"] == 4
    assert counts["displayed"] == 4
    assert counts["timed_out"] == 1
    assert counts["failed"] == 1


def test_displayable_response_requires_raw_content():
    assert _has_displayable_response(_resp("m1", content="hello")) is True
    assert _has_displayable_response(_resp("m1", content="")) is False
    assert _has_displayable_response(_resp("m1", success=False, content="hello")) is False


def test_meta_only_content_not_counted_for_analysis():
    meta_only = (
        "The user asks for a dog breed recommendation.\n\n"
        "We need to write a concise answer about Tokyo apartments."
    )
    results = [_resp("m1", content=meta_only)]
    counts = _count_council_responses(results)

    assert counts["displayed"] == 1
    assert counts["analysis"] == 0
