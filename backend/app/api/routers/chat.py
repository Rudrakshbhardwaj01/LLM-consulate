from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException

from app.api.dependencies import get_session_service, get_single_orchestrator
from app.config.constants import SESSION_HEADER
from app.schemas.chat import ChatRequest
from app.utils.errors import CLIENT_ERROR_MESSAGE
from app.utils.streaming import sse_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
):
    session_id = x_session_id or "anonymous"
    session = get_session_service()

    if not session.increment(session_id):
        raise HTTPException(
            status_code=429,
            detail="Session request limit reached. Start a fresh session.",
        )

    orchestrator = get_single_orchestrator()

    async def events() -> AsyncIterator[dict]:
        async for event in orchestrator.stream(request.model_id, request.messages):
            if event.type == "error":
                yield {"type": "error", "message": CLIENT_ERROR_MESSAGE}
                return
            if event.type == "chunk" and event.content:
                yield {"type": "chunk", "content": event.content}
            if event.type == "reasoning_chunk" and event.content:
                yield {"type": "reasoning_chunk", "content": event.content}
            if event.type == "done":
                yield {"type": "done"}

    return sse_response(events())
