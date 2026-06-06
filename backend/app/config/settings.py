import os
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to backend/ — not the process working directory.
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

_PLACEHOLDER_KEYS = frozenset({"", "your_nvidia_api_key_here", "changeme"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    synthesis_model_id: str = "gpt-oss-120b"
    session_request_limit: int = 15
    deadlock_threshold: float = 0.60
    consulate_model_timeout: float = Field(
        default=45.0,
        validation_alias=AliasChoices(
            "CONSULATE_MODEL_TIMEOUT",
            "COUNCIL_MEMBER_TIMEOUT_SECONDS",
        ),
    )

    judge_model_id: str = Field(
        default="gpt-oss-120b",
        validation_alias=AliasChoices("JUDGE_MODEL_ID", "SYNTHESIS_MODEL_ID"),
    )

    embedding_model_id: str = "nvidia/nv-embedqa-e5-v5"

    agreement_use_llm_claims: bool = False
    agreement_use_llm_judge: bool = False
    agreement_use_embeddings: bool = False
    agreement_use_llm: bool = False

    provider_max_retries: int = 3
    provider_timeout_seconds: float = 180.0
    provider_connect_timeout_seconds: float = 15.0

    cors_origins: str = "http://localhost:3000"
    app_name: str = "LLM Consulate"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @property
    def council_member_timeout_seconds(self) -> float:
        return self.consulate_model_timeout

    def council_timeout_info(self) -> tuple[float, str]:
        if os.environ.get("CONSULATE_MODEL_TIMEOUT"):
            return self.consulate_model_timeout, "env"
        if os.environ.get("COUNCIL_MEMBER_TIMEOUT_SECONDS"):
            return self.consulate_model_timeout, "env"
        return self.consulate_model_timeout, "default"

    @field_validator("nvidia_api_key", mode="before")
    @classmethod
    def strip_api_key(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def _looks_like_placeholder_key(self) -> bool:
        key = self.nvidia_api_key
        return (
            key.lower() in _PLACEHOLDER_KEYS or key.startswith("your_")
        )

    @property
    def nvidia_key_configured(self) -> bool:
        return bool(self.nvidia_api_key) and not self._looks_like_placeholder_key()

    @property
    def nvidia_key_diagnostics(self) -> dict[str, str | bool]:
        return {
            "env_file": str(ENV_FILE),
            "env_file_exists": ENV_FILE.exists(),
            "base_url": self.nvidia_base_url,
            "key_present": bool(self.nvidia_api_key),
            "key_detected": self.nvidia_key_configured,
            "looks_like_placeholder": self._looks_like_placeholder_key(),
        }

    @model_validator(mode="after")
    def validate_production_requirements(self) -> Self:
        if not self.is_production:
            return self

        errors: list[str] = []

        if not os.environ.get("NVIDIA_API_KEY", "").strip():
            errors.append(
                "NVIDIA_API_KEY must be set in the environment when APP_ENV=production."
            )
        elif not self.nvidia_key_configured:
            errors.append(
                "NVIDIA_API_KEY is missing or looks like a placeholder. "
                "Set a valid key in the environment when APP_ENV=production."
            )

        if not os.environ.get("CORS_ORIGINS", "").strip():
            errors.append(
                "CORS_ORIGINS must be set in the environment when APP_ENV=production "
                "(comma-separated frontend URLs). Do not rely on the localhost default."
            )
        else:
            origins = self.cors_origin_list
            if not origins:
                errors.append("CORS_ORIGINS is set but contains no valid origins.")
            elif all(
                "localhost" in o.lower() or "127.0.0.1" in o for o in origins
            ):
                errors.append(
                    "CORS_ORIGINS must include at least one non-localhost origin "
                    "when APP_ENV=production."
                )

        if errors:
            raise ValueError(
                "Production configuration error:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
