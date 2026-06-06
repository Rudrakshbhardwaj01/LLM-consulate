import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi.responses import StreamingResponse

from app.utils.errors import CLIENT_ERROR_MESSAGE
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def sse_generator(events: AsyncIterator[dict[str, Any]]) -> AsyncIterator[str]:
    try:
        async for event in events:
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        logger.exception("SSE stream failed")
        yield f"data: {json.dumps({'type': 'error', 'message': CLIENT_ERROR_MESSAGE})}\n\n"
        yield "data: [DONE]\n\n"


def sse_response(events: AsyncIterator[dict[str, Any]]) -> StreamingResponse:
    return StreamingResponse(
        sse_generator(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
