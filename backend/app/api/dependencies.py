from functools import lru_cache

from app.config.settings import Settings, get_settings
from app.orchestrator.consulate import ConsulateOrchestrator
from app.orchestrator.single_model import SingleModelOrchestrator
from app.orchestrator.synthesizer import Synthesizer
from app.providers.nvidia_provider import NvidiaProvider
from app.services.session import SessionService


@lru_cache
def get_provider() -> NvidiaProvider:
    return NvidiaProvider(get_settings())


@lru_cache
def get_session_service() -> SessionService:
    return SessionService(get_settings())


def get_single_orchestrator() -> SingleModelOrchestrator:
    return SingleModelOrchestrator(get_provider())


def get_consulate_orchestrator() -> ConsulateOrchestrator:
    settings = get_settings()
    provider = get_provider()
    return ConsulateOrchestrator(provider, Synthesizer(provider, settings), settings)


def get_app_settings() -> Settings:
    return get_settings()
