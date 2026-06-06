from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class MemoryConversation:
    id: str
    title: str


class MemoryConversationRepository:
    def __init__(self) -> None:
        self._store: dict[str, MemoryConversation] = {}

    async def create(self, title: str) -> MemoryConversation:
        conv = MemoryConversation(id=str(uuid4()), title=title)
        self._store[conv.id] = conv
        return conv

    async def get(self, conversation_id: str) -> MemoryConversation | None:
        return self._store.get(conversation_id)

    async def list_all(self) -> list[MemoryConversation]:
        return list(self._store.values())

    async def delete(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)


@dataclass
class MemorySessionRepository:
    _counts: dict[str, int] = field(default_factory=dict)

    async def get_request_count(self, session_id: str) -> int:
        return self._counts.get(session_id, 0)

    async def increment(self, session_id: str) -> int:
        self._counts[session_id] = self._counts.get(session_id, 0) + 1
        return self._counts[session_id]
