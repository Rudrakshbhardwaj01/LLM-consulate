from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException

from app.api.dependencies import get_consulate_orchestrator, get_session_service
from app.config.constants import SESSION_HEADER
from app.models.registry import get_council_members
from app.schemas.consulate import ConsulateRequest
from app.utils.streaming import sse_response

router = APIRouter(prefix="/consulate", tags=["consulate"])


@router.post("")
async def consulate(
    request: ConsulateRequest,
    x_session_id: str | None = Header(default=None, alias=SESSION_HEADER),
):
    council_ids = request.model_ids or [m.id for m in get_council_members()]

    if len(council_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="Consulate mode requires at least 2 council members",
        )

    session_id = x_session_id or "anonymous"
    session = get_session_service()

    if not session.increment(session_id):
        raise HTTPException(
            status_code=429,
            detail="Session request limit reached. Start a fresh session.",
        )

    orchestrator = get_consulate_orchestrator()

    async def events() -> AsyncIterator[dict]:
        async for event in orchestrator.stream(
            council_ids,
            request.messages,
            request.prompt,
            request.synthesis_model_id,
        ):
            yield event.to_sse_dict()

    return sse_response(events())
