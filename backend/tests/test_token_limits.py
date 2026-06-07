"""Tests for council and synthesis token limits."""

from app.config.constants import COUNCIL_MAX_TOKENS, SYNTHESIS_MAX_TOKENS
from app.config.settings import Settings
from app.orchestrator.synthesizer import Synthesizer
from app.providers.nvidia_provider import NvidiaProvider
from app.schemas.chat import ChatMessage


def test_settings_default_token_limits():
    settings = Settings()
    assert settings.council_max_tokens == COUNCIL_MAX_TOKENS == 384
    assert settings.synthesis_max_tokens == SYNTHESIS_MAX_TOKENS == 768


def test_council_payload_uses_council_max_tokens():
    provider = NvidiaProvider(Settings(nvidia_api_key="test-key-not-placeholder"))
    payload = provider._build_payload(
        "gpt-oss-120b",
        [ChatMessage.create("user", "hello")],
        stream=True,
        max_tokens=COUNCIL_MAX_TOKENS,
    )
    assert payload["max_tokens"] == 384


def test_synthesis_payload_uses_synthesis_max_tokens():
    provider = NvidiaProvider(Settings(nvidia_api_key="test-key-not-placeholder"))
    payload = provider._build_payload(
        "gpt-oss-120b",
        [ChatMessage.create("user", "hello")],
        stream=True,
        max_tokens=SYNTHESIS_MAX_TOKENS,
    )
    assert payload["max_tokens"] == 768


def test_synthesizer_reads_settings_max_tokens():
    settings = Settings(synthesis_max_tokens=768)
    synthesizer = Synthesizer(NvidiaProvider(settings), settings)
    assert synthesizer._synthesis_max_tokens == 768
