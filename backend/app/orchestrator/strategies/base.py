from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas.chat import ChatMessage
from app.schemas.consulate import ConsulateStreamEvent


class ConsulateContext(Protocol):
    model_ids: list[str]
    messages: list[ChatMessage]
    prompt: str
    synthesis_model_id: str


class ConsulateStrategy(Protocol):
    id: str
    name: str

    async def execute(
        self, ctx: ConsulateContext
    ) -> AsyncIterator[ConsulateStreamEvent]: ...


class DebateStrategy(ConsulateStrategy):
    """Future: adversarial debate between council members."""

    id = "debate"
    name = "Debate Mode"

    async def execute(self, ctx: ConsulateContext) -> AsyncIterator[ConsulateStreamEvent]:
        yield ConsulateStreamEvent(type="error", message="Debate Mode not implemented")
        return


class VotingStrategy(ConsulateStrategy):
    """Future: majority vote on best answer."""

    id = "voting"
    name = "Voting Mode"

    async def execute(self, ctx: ConsulateContext) -> AsyncIterator[ConsulateStreamEvent]:
        yield ConsulateStreamEvent(type="error", message="Voting Mode not implemented")
        return


class ExpertWitnessStrategy(ConsulateStrategy):
    """Future: route to specialized expert based on prompt."""

    id = "expert-witness"
    name = "Expert Witness Mode"

    async def execute(self, ctx: ConsulateContext) -> AsyncIterator[ConsulateStreamEvent]:
        yield ConsulateStreamEvent(
            type="error", message="Expert Witness Mode not implemented"
        )
        return


class ExpertRoutingStrategy(ConsulateStrategy):
    """Future: dynamic expert routing."""

    id = "expert-routing"
    name = "Expert Routing"

    async def execute(self, ctx: ConsulateContext) -> AsyncIterator[ConsulateStreamEvent]:
        yield ConsulateStreamEvent(
            type="error", message="Expert Routing not implemented"
        )
        return


class AdversarialReviewStrategy(ConsulateStrategy):
    """Future: one model reviews and challenges others."""

    id = "adversarial-review"
    name = "Adversarial Review"

    async def execute(self, ctx: ConsulateContext) -> AsyncIterator[ConsulateStreamEvent]:
        yield ConsulateStreamEvent(
            type="error", message="Adversarial Review not implemented"
        )
        return
