from fastapi import APIRouter

from app.models.registry import get_available_models
from app.schemas.models import ModelResponseSchema, ModelsListResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelsListResponse)
async def list_models():
    models = [
        ModelResponseSchema(
            id=m.id,
            displayName=m.display_name,
            provider=m.provider,
            role=m.role,
            description=m.description,
            contextLimit=m.max_tokens,
            capabilities=["chat", "reasoning"] if m.supports_reasoning else ["chat"],
            consulateEligible=m.consulate_eligible,
            family=m.family,
            tags=m.tags,
            openSource=True,
            supportsReasoning=m.supports_reasoning,
        )
        for m in get_available_models()
    ]
    return ModelsListResponse(models=models)
