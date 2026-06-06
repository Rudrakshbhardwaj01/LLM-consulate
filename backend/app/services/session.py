from app.config.settings import Settings


class SessionService:
    def __init__(self, settings: Settings) -> None:
        self._limit = settings.session_request_limit
        self._counts: dict[str, int] = {}

    def get_remaining(self, session_id: str) -> int:
        used = self._counts.get(session_id, 0)
        return max(0, self._limit - used)

    def is_exhausted(self, session_id: str) -> bool:
        return self._counts.get(session_id, 0) >= self._limit

    def increment(self, session_id: str) -> bool:
        if self.is_exhausted(session_id):
            return False
        self._counts[session_id] = self._counts.get(session_id, 0) + 1
        return True
