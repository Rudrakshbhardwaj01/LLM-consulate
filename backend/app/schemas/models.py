from pydantic import BaseModel, Field


class ModelResponseSchema(BaseModel):
    id: str
    display_name: str = Field(alias="displayName")
    provider: str
    role: str
    description: str
    context_limit: int = Field(alias="contextLimit")
    capabilities: list[str]
    consulate_eligible: bool = Field(alias="consulateEligible")
    family: str
    tags: list[str] = Field(default_factory=list)
    open_source: bool = Field(alias="openSource", default=True)
    supports_reasoning: bool = Field(alias="supportsReasoning", default=False)

    model_config = {"populate_by_name": True}


class ModelsListResponse(BaseModel):
    models: list[ModelResponseSchema]
