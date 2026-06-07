"""Tests for council workflow stage advancement."""

import pytest

from app.orchestrator.council_stage import (
    all_council_members_terminal,
    is_terminal_model_status,
    should_advance_to_analyzing,
)


@pytest.mark.parametrize(
    "status",
    ["complete", "completed", "error", "failed", "timeout"],
)
def test_terminal_model_statuses(status: str) -> None:
    assert is_terminal_model_status(status) is True


@pytest.mark.parametrize("status", ["pending", "running", "streaming"])
def test_non_terminal_model_statuses(status: str) -> None:
    assert is_terminal_model_status(status) is False


def test_all_council_members_terminal_when_mixed_outcomes() -> None:
    statuses = ["complete", "complete", "timeout", "error", "failed", "completed"]
    assert all_council_members_terminal(statuses) is True


def test_all_council_members_terminal_false_while_one_pending() -> None:
    statuses = ["complete", "complete", "pending", "timeout"]
    assert all_council_members_terminal(statuses) is False


def test_should_advance_to_analyzing_from_receiving() -> None:
    statuses = ["complete", "complete", "timeout", "failed"]
    assert should_advance_to_analyzing("receiving", statuses) is True


def test_should_not_advance_from_analyzing() -> None:
    statuses = ["complete", "timeout"]
    assert should_advance_to_analyzing("analyzing", statuses) is False


def test_should_not_advance_while_streaming() -> None:
    statuses = ["complete", "streaming"]
    assert should_advance_to_analyzing("receiving", statuses) is False
