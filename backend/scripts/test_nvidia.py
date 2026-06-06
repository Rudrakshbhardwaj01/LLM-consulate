"""Isolated NVIDIA API connectivity test — bypasses FastAPI and orchestration."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config.settings import get_settings  # noqa: E402


MODEL_ID = "openai/gpt-oss-120b"
PROMPT = "Reply with exactly the word SUCCESS and nothing else."


def print_config(settings) -> None:
    diag = settings.nvidia_key_diagnostics
    print("=== NVIDIA configuration ===")
    print(f"env_file: {diag['env_file']}")
    print(f"env_file_exists: {diag['env_file_exists']}")
    print(f"NVIDIA_BASE_URL: {diag['base_url']}")
    print(f"key_present: {diag['key_present']}")
    print(f"key_length: {diag['key_length']}")
    if diag["key_present"]:
        print(f"key_prefix: {diag['key_prefix']}")
        print(f"key_suffix: {diag['key_suffix']}")
    print(f"looks_like_placeholder: {diag['looks_like_placeholder']}")
    print(f"model: {MODEL_ID}")
    print()


async def run_test() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    print_config(settings)

    key = settings.nvidia_api_key
    if not key:
        print("FAILURE")
        print("NVIDIA_API_KEY is missing. Set it in backend/.env")
        return 1

    if settings.nvidia_key_diagnostics["looks_like_placeholder"]:
        print("FAILURE")
        print("NVIDIA_API_KEY appears to be a placeholder, not a real key.")
        return 1

    url = f"{settings.nvidia_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 32,
        "temperature": 0.2,
        "stream": False,
    }

    print("=== Request ===")
    print(f"URL: {url}")
    print(f"Auth header starts with Bearer: {headers['Authorization'].startswith('Bearer ')}")
    print(f"Auth token empty: {len(key) == 0}")
    print(f"Payload model: {payload['model']}")
    print()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        print("=== Response ===")
        print(f"status: {response.status_code}")
        for header in ("x-request-id", "nv-request-id", "x-amzn-requestid"):
            if header in response.headers:
                print(f"{header}: {response.headers[header]}")

        body = response.text
        print(f"body: {body[:2000]}")

        if response.status_code >= 400:
            print()
            print("FAILURE")
            try:
                parsed = response.json()
                detail = parsed.get("detail") or parsed.get("error")
                print(f"NVIDIA error detail: {detail}")
            except json.JSONDecodeError:
                pass
            return 1

        parsed = response.json()
        message = parsed.get("choices", [{}])[0].get("message", {})
        content = message.get("content") or message.get("reasoning") or message.get("reasoning_content") or ""
        print()
        print("SUCCESS")
        print(f"model_response: {content[:200]}")
        return 0

    except Exception as exc:
        print()
        print("FAILURE")
        print(f"exception: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_test()))
