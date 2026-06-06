"""Strip internal reasoning and planning text from model outputs before council analysis."""

import re

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Block tags used by reasoning models (content inside is never council-facing).
_THINK_BLOCK_RE = re.compile(
    r"<\s*(?:think|thinking|reasoning|analysis)\s*>[\s\S]*?"
    r"<\s*/\s*(?:think|thinking|reasoning|analysis)\s*>",
    re.IGNORECASE,
)

# Lines that are clearly meta-planning, not user-facing answers.
_REASONING_LINE_RE = re.compile(
    r"^\s*(?:"
    r"(?:the\s+)?user\s+(?:asks|is\s+asking|wants|requested|has\s+asked)"
    r"|(?:we|i)\s+(?:need|should|must|will|have)\s+to"
    r"|let(?:'s|\s+me)\s+(?:think|consider|analyze|write|draft|start|begin)"
    r"|(?:i(?:'ll|\s+will|\s+should|\s+need\s+to))\s+(?:write|draft|provide|answer|respond|start|begin|cover)"
    r"|(?:first|next|now),?\s+(?:i|we)\s+(?:need|should|will|must)"
    r"|(?:this\s+(?:is\s+a|requires)\s+(?:simple|straightforward|brief))"
    r"|(?:planning|analysis|approach)\s*:"
    r"|(?:step\s+\d+)"
    r")\b",
    re.IGNORECASE,
)

# Paragraphs that are entirely meta commentary.
_META_PARAGRAPH_RE = re.compile(
    r"^(?:"
    r"(?:the\s+)?user(?:'s)?\s+(?:question|prompt|request)"
    r"|(?:we|i)\s+(?:need|should)\s+to"
    r"|(?:let(?:'s|\s+me)\s+(?:think|write))"
    r")",
    re.IGNORECASE | re.MULTILINE,
)


def sanitize_council_content(content: str, reasoning: str | None = None) -> str:
    """
    Return only the user-facing answer text for council agreement analysis.

    Reasoning traces are never included. When models embed planning inside
    ``content``, strip it and keep substantive answer paragraphs.
    """
    raw = (content or "").strip()
    if not raw:
        logger.debug("consulate.sanitize | empty content, skipping reasoning fallback")
        return ""

    text = _THINK_BLOCK_RE.sub("", raw)
    text = re.sub(r"<\s*/?\s*(?:think|thinking|reasoning|analysis)\s*>", "", text, flags=re.IGNORECASE)
    text = text.strip()

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return ""

    substantive = [p for p in paragraphs if not _is_meta_paragraph(p)]
    if substantive:
        result = "\n\n".join(substantive)
    else:
        # Fall back to longest non-meta line block if everything looked like planning.
        result = max(paragraphs, key=len)

    result = _strip_reasoning_lines(result).strip()
    if not result:
        logger.warning(
            "consulate.sanitize | all content filtered as meta | raw_chars=%d",
            len(raw),
        )
        return ""

    if reasoning:
        logger.debug(
            "consulate.sanitize | excluded reasoning_chars=%d from council analysis",
            len(reasoning),
        )

    if len(result) < len(raw):
        logger.debug(
            "consulate.sanitize | raw_chars=%d sanitized_chars=%d",
            len(raw),
            len(result),
        )

    return result


def _is_meta_paragraph(paragraph: str) -> bool:
    lines = [ln.strip() for ln in paragraph.splitlines() if ln.strip()]
    if not lines:
        return True
    meta_lines = sum(1 for ln in lines if _REASONING_LINE_RE.search(ln) or _META_PARAGRAPH_RE.match(ln))
    return meta_lines >= len(lines)


def _strip_reasoning_lines(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        if _REASONING_LINE_RE.search(stripped):
            continue
        if _META_PARAGRAPH_RE.match(stripped):
            continue
        kept.append(line)
    return "\n".join(kept).strip()
