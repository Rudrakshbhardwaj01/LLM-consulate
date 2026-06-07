"""Tests for ConsulateStreamEvent status field separation."""

import pytest
from pydantic import ValidationError

from app.schemas.consulate import ConsulateStreamEvent


@pytest.mark.parametrize(
    "model_status",
    ["pending", "running", "streaming", "completed", "complete", "failed", "error", "timeout"],
)
def test_model_status_events_accept_lifecycle_values(model_status: str) -> None:
    event = ConsulateStreamEvent(
        type="model_status",
        modelId="gpt-oss-120b",
        model_status=model_status,
    )
    assert event.model_status == model_status
    assert event.synthesis_status is None

    sse = event.to_sse_dict()
    assert sse["modelStatus"] == model_status
    assert sse["status"] == model_status


@pytest.mark.parametrize("synthesis_status", ["ok", "degraded"])
def test_synthesis_complete_events_accept_synthesis_status(
    synthesis_status: str,
) -> None:
    event = ConsulateStreamEvent(
        type="synthesis_complete",
        content="Council summary",
        synthesis_status=synthesis_status,
        deadlock=synthesis_status == "degraded",
    )
    assert event.synthesis_status == synthesis_status
    assert event.model_status is None

    sse = event.to_sse_dict()
    assert sse["synthesisStatus"] == synthesis_status
    assert sse["status"] == synthesis_status


def test_pending_model_status_does_not_raise() -> None:
    """Regression: pending must not fail validation (production outage)."""
    event = ConsulateStreamEvent(
        type="model_status",
        model_id="nemotron-omni-30b",
        model_status="pending",
    )
    assert event.model_status == "pending"


def test_degraded_synthesis_does_not_conflict_with_model_status() -> None:
    event = ConsulateStreamEvent(
        type="synthesis_complete",
        content="Fallback answer",
        answer="Fallback answer",
        synthesis_status="degraded",
        synthesis_degraded=True,
        deadlock=True,
    )
    sse = event.to_sse_dict()
    assert sse["synthesisStatus"] == "degraded"
    assert sse["status"] == "degraded"
    assert sse["answer"] == "Fallback answer"


def test_invalid_status_value_rejected_on_model_status_field() -> None:
    with pytest.raises(ValidationError):
        ConsulateStreamEvent(
            type="model_status",
            modelId="gpt-oss-120b",
            model_status="degraded",  # type: ignore[arg-type]
        )


def test_invalid_status_value_rejected_on_synthesis_status_field() -> None:
    with pytest.raises(ValidationError):
        ConsulateStreamEvent(
            type="synthesis_complete",
            synthesis_status="pending",  # type: ignore[arg-type]
        )
