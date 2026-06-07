"""Central guards for provider-bound chat messages."""

from app.schemas.chat import MAX_MESSAGE_CHARS, ChatMessage, guard_message_content
from app.utils.logging import get_logger

logger = get_logger(__name__)


def ensure_message_list(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Return messages with every content field within schema limits."""
    guarded: list[ChatMessage] = []
    for message in messages:
        safe_content, truncated = guard_message_content(message.content)
        if truncated:
            logger.warning(
                "chat.message.truncated | role=%s | original_chars=%d | limit=%d",
                message.role,
                len(message.content),
                MAX_MESSAGE_CHARS,
            )
            guarded.append(ChatMessage.create(message.role, safe_content))
        else:
            guarded.append(message)
    return guarded


def assert_messages_within_limit(messages: list[ChatMessage]) -> None:
    """Hard safety check immediately before model invocation."""
    for message in messages:
        assert len(message.content) <= MAX_MESSAGE_CHARS, (
            f"ChatMessage content exceeds limit: role={message.role} "
            f"len={len(message.content)} max={MAX_MESSAGE_CHARS}"
        )
