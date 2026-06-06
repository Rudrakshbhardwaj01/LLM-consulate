from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    model_id: str = Field(alias="modelId")
    model_name: str = Field(default="", alias="modelName")
    role: str = ""
    content: str = ""
    reasoning: str | None = None
    latency_ms: int = Field(alias="latencyMs", default=0)
    success: bool = True
    error: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def effective_content(self) -> str:
        """User-facing answer only. Reasoning traces are never council input."""
        from app.orchestrator.content_sanitizer import sanitize_council_content

        return sanitize_council_content(self.content, self.reasoning)
