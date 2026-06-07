from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.chat import ChatMessage, MAX_CONVERSATION_MESSAGES, MAX_MESSAGE_CHARS

SynthesisStatus = Literal["ok", "degraded"]


class ConsulateRequest(BaseModel):
    model_ids: list[str] = Field(default_factory=list, alias="modelIds")
    messages: list[ChatMessage] = Field(
        default_factory=list, max_length=MAX_CONVERSATION_MESSAGES
    )
    prompt: str = Field(max_length=MAX_MESSAGE_CHARS)
    synthesis_model_id: str | None = Field(default=None, alias="synthesisModelId")

    model_config = {"populate_by_name": True}


ConsulateStage = Literal[
    "initializing",
    "receiving",
    "analyzing",
    "synthesizing",
    "complete",
    "deadlock",
    "error",
]
ModelStatus = Literal["pending", "streaming", "complete", "error", "timeout"]


class DisagreementSummary(BaseModel):
    disputed_concept: str = Field(default="", alias="disputedConcept")
    majority_position: str = Field(default="", alias="majorityPosition")
    minority_position: str = Field(default="", alias="minorityPosition")
    majority_support: float = Field(default=0.0, alias="majoritySupport")
    minority_support: float = Field(default=0.0, alias="minoritySupport")
    explanation: str = ""

    model_config = {"populate_by_name": True}


class MinorityReport(BaseModel):
    model: str
    model_id: str = Field(alias="modelId")
    role: str = ""
    response: str
    reasoning: str | None = None

    model_config = {"populate_by_name": True}


class ConsulateStreamEvent(BaseModel):
    type: str
    stage: ConsulateStage | None = None
    model_id: str | None = Field(default=None, alias="modelId")
    status: ModelStatus | None = None
    content: str | None = None
    reasoning: str | None = None
    error: str | None = None
    message: str | None = None
    agreement_score: float | None = Field(default=None, alias="agreementScore")
    majority_position: str | None = Field(default=None, alias="majorityPosition")
    minority_position: str | None = Field(default=None, alias="minorityPosition")
    minority_report: MinorityReport | None = Field(default=None, alias="minorityReport")
    latency_ms: int | None = Field(default=None, alias="latencyMs")
    council_total: int | None = Field(default=None, alias="councilTotal")
    council_responded: int | None = Field(default=None, alias="councilResponded")
    primary_disagreement: str | None = Field(default=None, alias="primaryDisagreement")
    majority_support: float | None = Field(default=None, alias="majoritySupport")
    minority_support: float | None = Field(default=None, alias="minoritySupport")
    supporting_models: list[str] | None = Field(default=None, alias="supportingModels")
    minority_models: list[str] | None = Field(default=None, alias="minorityModels")
    disagreement: DisagreementSummary | None = None
    is_consensus: bool | None = Field(default=None, alias="isConsensus")
    consensus_outcome: str | None = Field(default=None, alias="consensusOutcome")
    outcome_label: str | None = Field(default=None, alias="outcomeLabel")
    confidence_level: str | None = Field(default=None, alias="confidenceLevel")
    status: SynthesisStatus | None = None
    deadlock: bool | None = None
    synthesis_degraded: bool | None = Field(default=None, alias="synthesisDegraded")
    answer: str | None = None

    model_config = {"populate_by_name": True}

    def to_sse_dict(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True, exclude_none=True)
        if self.content is not None and "answer" not in data:
            data["answer"] = self.content
        return data
