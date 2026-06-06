from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, consulate, health, models
from app.config.settings import get_settings
from app.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _log_nvidia_diagnostics(settings) -> None:
    diag = settings.nvidia_key_diagnostics
    logger.info("NVIDIA env file: %s (exists=%s)", diag["env_file"], diag["env_file_exists"])
    logger.info("NVIDIA_BASE_URL: %s", diag["base_url"])
    logger.info("NVIDIA key detected: %s", diag["key_detected"])

    if diag["looks_like_placeholder"]:
        logger.error(
            "NVIDIA_API_KEY looks like a placeholder — replace it in backend/.env"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    get_settings.cache_clear()
    settings = get_settings()
    _log_nvidia_diagnostics(settings)

    if settings.nvidia_key_configured:
        logger.info("LLM Consulate API started — NVIDIA provider configured")
    elif settings.is_production:
        logger.warning("LLM Consulate API started — NVIDIA provider not configured")

    yield


settings = get_settings()

app = FastAPI(
    title="LLM Consulate API",
    description="Multi-model AI orchestration — council consensus platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(models.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(consulate.router, prefix=API_PREFIX)
