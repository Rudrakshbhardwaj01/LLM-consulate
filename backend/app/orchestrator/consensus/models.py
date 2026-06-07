"""Typed models for the semantic consensus pipeline."""

from pydantic import BaseModel, Field

from app.schemas.consulate import DisagreementSummary, MinorityReport


class ExtractedClaims(BaseModel):
    """Structured representation of a single council response."""

    model_id: str = Field(alias="modelId")
    model_name: str = Field(default="", alias="modelName")
    topic: str = ""
    interpretation: str = ""
    position_key: str = Field(default="", alias="positionKey")
    position_summary: str = Field(default="", alias="positionSummary")
    claims: list[str] = Field(default_factory=list)
    sanitized_text: str = Field(default="", alias="sanitizedText")

    model_config = {"populate_by_name": True}


class PositionCluster(BaseModel):
    """A group of models sharing the same semantic position."""

    position_key: str = Field(alias="positionKey")
    position_label: str = Field(alias="positionLabel")
    position_summary: str = Field(alias="positionSummary")
    model_ids: list[str] = Field(default_factory=list, alias="modelIds")
    model_names: list[str] = Field(default_factory=list, alias="modelNames")
    count: int = 0
    support: float = 0.0

    model_config = {"populate_by_name": True}


class JudgeVerdict(BaseModel):
    """Second-pass LLM judge output."""

    fundamentally_agree: bool = False
    majority_position: str = Field(default="", alias="majorityPosition")
    minority_positions: list[str] = Field(default_factory=list, alias="minorityPositions")
    confidence: float = 0.0
    disputed_concept: str = Field(default="", alias="disputedConcept")
    explanation: str = ""
    source: str = "heuristic"

    model_config = {"populate_by_name": True}


class AgreementTiming(BaseModel):
    """Per-stage latency for agreement analysis (milliseconds)."""

    claim_extraction_ms: int = Field(default=0, alias="claimExtractionMs")
    embeddings_ms: int = Field(default=0, alias="embeddingsMs")
    similarity_ms: int = Field(default=0, alias="similarityMs")
    cluster_ms: int = Field(default=0, alias="clusterMs")
    cluster_merge_ms: int = Field(default=0, alias="clusterMergeMs")
    majority_ms: int = Field(default=0, alias="majorityMs")
    judge_ms: int = Field(default=0, alias="judgeMs")
    total_ms: int = Field(default=0, alias="totalMs")

    model_config = {"populate_by_name": True}


class ConsensusResult(BaseModel):
    """Final output of the agreement engine."""

    agreement_score: float = Field(alias="agreementScore")
    is_deadlock: bool = Field(alias="isDeadlock")
    consensus_outcome: str = Field(default="consensus_moderate", alias="consensusOutcome")
    outcome_label: str = Field(default="Moderate Consensus", alias="outcomeLabel")
    confidence_level: str = Field(default="moderate", alias="confidenceLevel")
    majority_position: str = Field(alias="majorityPosition")
    minority_position: str = Field(default="", alias="minorityPosition")
    primary_disagreement: str = Field(default="", alias="primaryDisagreement")
    majority_support: float = Field(default=0.0, alias="majoritySupport")
    minority_support: float = Field(default=0.0, alias="minoritySupport")
    supporting_models: list[str] = Field(default_factory=list, alias="supportingModels")
    minority_models: list[str] = Field(default_factory=list, alias="minorityModels")
    disagreement: DisagreementSummary | None = None
    extracted_claims: list[ExtractedClaims] = Field(default_factory=list, alias="extractedClaims")
    clusters: list[PositionCluster] = Field(default_factory=list)
    judge_verdict: JudgeVerdict | None = Field(default=None, alias="judgeVerdict")
    embedding_similarity: float = Field(default=0.0, alias="embeddingSimilarity")
    majority_vote_component: float = Field(default=0.0, alias="majorityVoteComponent")
    judge_component: float = Field(default=0.0, alias="judgeComponent")
    embedding_component: float = Field(default=0.0, alias="embeddingComponent")
    minority_reports: list[MinorityReport] = Field(default_factory=list)
    timing: AgreementTiming | None = None

    model_config = {"populate_by_name": True}
