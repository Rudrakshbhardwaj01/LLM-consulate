from typing import Literal

from pydantic import BaseModel, Field

ProviderId = Literal["nvidia"]


class ModelDefinition(BaseModel):
    id: str
    display_name: str = Field(alias="displayName")
    provider: ProviderId = "nvidia"
    provider_model_id: str
    role: str
    description: str
    enabled: bool = True
    supports_reasoning: bool = Field(alias="supportsReasoning", default=False)
    max_tokens: int = Field(alias="maxTokens", default=4096)
    temperature: float = 0.7
    top_p: float = Field(alias="topP", default=0.9)
    consulate_eligible: bool = True
    family: str = ""
    tags: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
