import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient(timeout=90) as client:
        async with client.stream(
            "POST",
            "http://127.0.0.1:8000/api/chat",
            json={
                "modelId": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "Reply with one word: SUCCESS"}],
            },
            headers={"X-Session-Id": "final-verify-2"},
        ) as response:
            body = ""
            async for chunk in response.aiter_text():
                body += chunk

    has_error = '"type": "error"' in body
    has_success = "SUCCESS" in body
    has_done = "[DONE]" in body
    print(f"HTTP streaming completed")
    print(f"error_event={has_error}")
    print(f"success_content={has_success}")
    print(f"done_marker={has_done}")
    if has_error:
        idx = body.find('"type": "error"')
        print(body[idx : idx + 120])


if __name__ == "__main__":
    asyncio.run(main())
