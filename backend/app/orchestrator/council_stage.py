"""Council workflow stage helpers."""

from __future__ import annotations

TERMINAL_MODEL_STATUSES = frozenset(
    {
        "complete",
        "completed",
        "error",
        "failed",
        "timeout",
    }
)


def is_terminal_model_status(status: str) -> bool:
    return status in TERMINAL_MODEL_STATUSES


def all_council_members_terminal(statuses: list[str]) -> bool:
    return bool(statuses) and all(is_terminal_model_status(status) for status in statuses)


def should_advance_to_analyzing(current_stage: str, statuses: list[str]) -> bool:
    return current_stage == "receiving" and all_council_members_terminal(statuses)
