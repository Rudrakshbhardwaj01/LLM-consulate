import asyncio

import json

import time

from collections.abc import AsyncIterator



import httpx



from app.config.settings import Settings

from app.models.registry import get_model

from app.orchestrator.message_guard import assert_messages_within_limit, ensure_message_list
from app.schemas.chat import ChatMessage

from app.schemas.provider import ModelResponse

from app.utils.errors import ProviderError

from app.utils.logging import get_logger



logger = get_logger(__name__)



RETRYABLE_STATUS = {429, 500, 502, 503, 504}





class NvidiaProvider:

    def __init__(self, settings: Settings) -> None:

        self._settings = settings

        self._log_init_diagnostics()



    def _log_init_diagnostics(self) -> None:
        logger.info(
            "NvidiaProvider initialized | base_url=%s | configured=%s",
            self._settings.nvidia_base_url.rstrip("/"),
            self._settings.nvidia_key_configured,
        )



    def is_configured(self) -> bool:
        key = self._settings.nvidia_api_key
        if not key:
            return False
        return not self._settings.nvidia_key_diagnostics["looks_like_placeholder"]

    def _headers(self) -> dict[str, str]:
        key = self._settings.nvidia_api_key.strip()
        auth = f"Bearer {key}"
        if not key:
            raise ProviderError("NVIDIA API key is empty")
        if not auth.startswith("Bearer ") or auth == "Bearer ":
            raise ProviderError("Malformed Authorization header: missing token")
        return {
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

    def _timeout(self) -> httpx.Timeout:

        return httpx.Timeout(

            self._settings.provider_timeout_seconds,

            connect=self._settings.provider_connect_timeout_seconds,

        )



    def _build_payload(

        self,
        model_id: str,
        messages: list[ChatMessage],
        stream: bool,
        max_tokens: int | None = None,
    ) -> dict:

        model = get_model(model_id)

        if not model:

            raise ProviderError(f"Model not found: {model_id}")



        payload = {

            "model": model.provider_model_id,

            "messages": [m.model_dump() for m in messages],

            "stream": stream,

            "temperature": model.temperature,

            "top_p": model.top_p,

            "max_tokens": max_tokens if max_tokens is not None else model.max_tokens,

        }

        logger.info(
            "consulate.tokens | model=%s | max_tokens=%s",
            model_id,
            payload["max_tokens"],
        )

        logger.debug(

            "NVIDIA payload for %s -> model=%r temperature=%s top_p=%s max_tokens=%s",

            model_id,

            payload["model"],

            payload["temperature"],

            payload["top_p"],

            payload["max_tokens"],

        )

        return payload



    def _extract_delta(self, parsed: dict) -> tuple[str | None, str | None]:

        choices = parsed.get("choices") or []

        if not choices:

            return None, None

        delta = choices[0].get("delta", {}) or {}

        content = delta.get("content")

        reasoning = (

            delta.get("reasoning_content")

            or delta.get("reasoning")

            or delta.get("thinking")

        )

        return content, reasoning



    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float:

        if response is not None:

            retry_after = response.headers.get("Retry-After")

            if retry_after:

                try:

                    return min(float(retry_after), 30.0)

                except ValueError:

                    pass

        return min(2**attempt, 16.0)



    def _log_error_response(

        self,

        model_id: str,

        response: httpx.Response,

        body: bytes,

    ) -> None:

        text = body.decode(errors="replace")

        request_id = (

            response.headers.get("x-request-id")

            or response.headers.get("nv-request-id")

            or response.headers.get("x-amzn-requestid")

        )

        logger.error(

            "NVIDIA API error | model=%s | status=%s | request_id=%s | body=%s",

            model_id,

            response.status_code,

            request_id or "n/a",

            text[:2000],

        )



    async def stream_chat(

        self,

        model_id: str,

        messages: list[ChatMessage],

        max_tokens: int | None = None,

    ) -> AsyncIterator[tuple[str, str | None]]:

        if not self.is_configured():

            raise ProviderError(

                "NVIDIA API key is not configured. Set NVIDIA_API_KEY in backend/.env"

            )

        messages = ensure_message_list(messages)
        assert_messages_within_limit(messages)

        url = f"{self._settings.nvidia_base_url.rstrip('/')}/chat/completions"

        payload = self._build_payload(model_id, messages, stream=True, max_tokens=max_tokens)

        max_retries = self._settings.provider_max_retries



        async with httpx.AsyncClient(timeout=self._timeout()) as client:

            for attempt in range(max_retries):

                try:

                    async with client.stream(

                        "POST", url, headers=self._headers(), json=payload

                    ) as response:

                        if response.status_code in RETRYABLE_STATUS:

                            if attempt < max_retries - 1:

                                delay = self._retry_delay(attempt, response)

                                logger.warning(

                                    "NVIDIA retryable status %d for %s (attempt %d), waiting %.1fs",

                                    response.status_code,

                                    model_id,

                                    attempt + 1,

                                    delay,

                                )

                                await asyncio.sleep(delay)

                                continue

                            body = await response.aread()

                            self._log_error_response(model_id, response, body)

                            raise ProviderError(

                                f"NVIDIA API error ({response.status_code}): {body.decode()}"

                            )



                        if response.status_code >= 400:

                            body = await response.aread()

                            self._log_error_response(model_id, response, body)

                            raise ProviderError(

                                f"NVIDIA API error ({response.status_code}): {body.decode()}"

                            )



                        buffer = ""

                        async for chunk in response.aiter_text():

                            buffer += chunk

                            while "\n" in buffer:

                                line, buffer = buffer.split("\n", 1)

                                line = line.strip()

                                if not line or not line.startswith("data: "):

                                    continue

                                data = line[6:]

                                if data == "[DONE]":

                                    return

                                try:

                                    parsed = json.loads(data)

                                    content, reasoning = self._extract_delta(parsed)

                                    if content:

                                        yield content, None

                                    if reasoning:

                                        yield "", reasoning

                                except json.JSONDecodeError:

                                    continue

                        line = buffer.strip()

                        if line.startswith("data: "):

                            data = line[6:]

                            if data != "[DONE]":

                                try:

                                    parsed = json.loads(data)

                                    content, reasoning = self._extract_delta(parsed)

                                    if content:

                                        yield content, None

                                    if reasoning:

                                        yield "", reasoning

                                except json.JSONDecodeError:

                                    pass

                        return

                except httpx.TimeoutException as exc:

                    if attempt < max_retries - 1:

                        delay = self._retry_delay(attempt, None)

                        logger.warning(

                            "NVIDIA timeout for %s (attempt %d), waiting %.1fs",

                            model_id,

                            attempt + 1,

                            delay,

                        )

                        await asyncio.sleep(delay)

                        continue

                    raise ProviderError(f"NVIDIA request timed out: {exc}") from exc

                except httpx.RequestError as exc:

                    if attempt < max_retries - 1:

                        delay = self._retry_delay(attempt, None)

                        logger.warning(

                            "NVIDIA request failed for %s (attempt %d): %s",

                            model_id,

                            attempt + 1,

                            exc,

                        )

                        await asyncio.sleep(delay)

                        continue

                    raise ProviderError(f"NVIDIA request failed: {exc}") from exc

    async def embedding_similarity(
        self,
        texts: list[str],
        embedding_model_id: str,
    ) -> float:
        """Mean pairwise cosine similarity using NVIDIA embeddings API."""
        if len(texts) < 2:
            return 1.0

        if not self.is_configured():
            raise ProviderError("NVIDIA API key is not configured")

        url = f"{self._settings.nvidia_base_url.rstrip('/')}/embeddings"
        payload = {
            "model": embedding_model_id,
            "input": texts,
            "encoding_format": "float",
        }

        async with httpx.AsyncClient(timeout=self._timeout()) as client:
            response = await client.post(
                url, headers=self._headers(), json=payload
            )
            if response.status_code >= 400:
                self._log_error_response(embedding_model_id, response, response.content)
                raise ProviderError(
                    f"NVIDIA embeddings error ({response.status_code}): {response.text[:500]}"
                )

            data = response.json()
            vectors: list[list[float]] = []
            for item in sorted(data.get("data", []), key=lambda x: x.get("index", 0)):
                vectors.append(item.get("embedding", []))

            if len(vectors) < 2:
                raise ProviderError("Insufficient embedding vectors returned")

            pairwise: list[float] = []
            for i in range(len(vectors)):
                for j in range(i + 1, len(vectors)):
                    pairwise.append(_cosine_similarity(vectors[i], vectors[j]))

            return sum(pairwise) / len(pairwise) if pairwise else 1.0

    async def invoke(

        self,

        model_id: str,

        messages: list[ChatMessage],

        max_tokens: int | None = None,

    ) -> ModelResponse:

        model = get_model(model_id)

        if not model:

            return ModelResponse(

                modelId=model_id,

                success=False,

                error=f"Model not found: {model_id}",

            )



        if not self.is_configured():

            return ModelResponse(

                modelId=model_id,

                modelName=model.display_name,

                role=model.role,

                success=False,

                error="NVIDIA API key is not configured",

            )



        start = time.perf_counter()

        content_parts: list[str] = []

        reasoning_parts: list[str] = []



        try:

            async for content, reasoning in self.stream_chat(
                model_id, messages, max_tokens=max_tokens
            ):

                if content:

                    content_parts.append(content)

                if reasoning:

                    reasoning_parts.append(reasoning)



            latency = int((time.perf_counter() - start) * 1000)

            logger.info(

                "Model %s responded in %dms (%d chars)",

                model_id,

                latency,

                len("".join(content_parts)),

            )



            return ModelResponse(

                modelId=model_id,

                modelName=model.display_name,

                role=model.role,

                content="".join(content_parts),

                reasoning="".join(reasoning_parts) or None,

                latencyMs=latency,

                success=True,

            )

        except ProviderError as exc:

            latency = int((time.perf_counter() - start) * 1000)

            logger.error("Model %s failed after %dms: %s", model_id, latency, exc)

            return ModelResponse(

                modelId=model_id,

                modelName=model.display_name,

                role=model.role,

                latencyMs=latency,

                success=False,

                error=str(exc),

            )


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    import math

    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
