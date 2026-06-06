from fastapi import APIRouter

from app.api.dependencies import get_provider
from app.config.settings import get_settings
from app.models.registry import get_council_members

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    provider = get_provider()
    council = get_council_members()
    return {
        "status": "ok",
        "service": settings.app_name,
        "provider": "nvidia",
        "provider_configured": provider.is_configured(),
        "council_members": len(council),
    }
