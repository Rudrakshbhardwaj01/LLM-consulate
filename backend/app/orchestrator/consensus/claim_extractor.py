"""Extract structured claims and interpretations from council responses."""

import json
import re

from app.orchestrator.content_sanitizer import sanitize_council_content
from app.orchestrator.consensus.models import ExtractedClaims
from app.providers.nvidia_provider import NvidiaProvider
from app.orchestrator.synthesis_prompt import truncate_text
from app.schemas.chat import ChatMessage
from app.schemas.provider import ModelResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

CLAIM_EXTRACTION_PROMPT = """You extract structured meaning from a council member's answer.
Ignore writing style, formatting, verbosity, and tone. Focus only on semantic content.

Return ONLY valid JSON with this shape:
{
  "topic": "main subject",
  "interpretation": "primary interpretation or framing (short slug, e.g. soccer, american_football)",
  "position_summary": "one sentence overall position",
  "claims": ["factual claim 1", "factual claim 2"]
}"""

# Heuristic signals for common ambiguous topics (extensible without LLM).
_AMERICAN_FOOTBALL_SIGNALS = (
    "american football",
    "nfl",
    "quarterback",
    "touchdown",
    "touchdowns",
    "super bowl",
    "downs",
    "line of scrimmage",
    "linebacker",
    "pigskin",
    "gridiron",
    "end zone",
    "field goal",
    "yard line",
    "oval ball",
)

_SOCCER_SIGNALS = (
    "soccer",
    "association football",
    "pitch",
    "goalkeeper",
    "striker",
    "premier league",
    "fifa",
    "90 minute",
    "90-minute",
    "mls",
    "world cup",
    "uefa",
    "champions league",
    "penalty kick",
    "offside",
)


def extract_claims_heuristic(
    response: ModelResponse,
    sanitized: str,
    prompt: str,
) -> ExtractedClaims:
    """Rule-based claim extraction — always available, no API call."""
    topic = _infer_topic(prompt, sanitized)
    interpretation, position_key = _infer_interpretation(topic, sanitized)
    claims = _extract_factual_claims(sanitized)
    position_summary = _build_position_summary(interpretation, claims, sanitized)

    return ExtractedClaims(
        modelId=response.model_id,
        modelName=response.model_name,
        topic=topic,
        interpretation=interpretation,
        positionKey=position_key,
        positionSummary=position_summary,
        claims=claims,
        sanitizedText=sanitized,
    )


async def extract_claims_llm(
    provider: NvidiaProvider,
    judge_model_id: str,
    response: ModelResponse,
    sanitized: str,
    prompt: str,
) -> ExtractedClaims | None:
    """Optional LLM claim extraction when provider is configured."""
    if not provider.is_configured():
        return None

    excerpt = truncate_text(sanitized, 6000)
    user_content = (
        f"User question:\n{truncate_text(prompt, 1500)}\n\n"
        f"Council member ({response.model_name}) response:\n{excerpt}"
    )
    messages = [
        ChatMessage.create("system", CLAIM_EXTRACTION_PROMPT),
        ChatMessage.create("user", user_content),
    ]

    try:
        result = await provider.invoke(judge_model_id, messages)
        if not result.success or not result.effective_content:
            return None
        parsed = _parse_json_block(result.effective_content)
        if not parsed:
            return None

        interpretation = str(parsed.get("interpretation", "")).strip()
        position_key = _normalize_position_key(interpretation or parsed.get("position_summary", ""))

        return ExtractedClaims(
            modelId=response.model_id,
            modelName=response.model_name,
            topic=str(parsed.get("topic", "")).strip() or _infer_topic(prompt, sanitized),
            interpretation=interpretation,
            positionKey=position_key,
            positionSummary=str(parsed.get("position_summary", "")).strip(),
            claims=[str(c).strip() for c in parsed.get("claims", []) if str(c).strip()],
            sanitizedText=sanitized,
        )
    except Exception as exc:
        logger.warning(
            "consulate.claims.llm_failed | model=%s | error=%s",
            response.model_id,
            exc,
        )
        return None


async def extract_all_claims(
    provider: NvidiaProvider | None,
    judge_model_id: str,
    responses: list[ModelResponse],
    prompt: str,
    use_llm: bool = True,
) -> list[ExtractedClaims]:
    """Extract claims for every successful response."""
    extracted: list[ExtractedClaims] = []

    for resp in responses:
        sanitized = sanitize_council_content(resp.content, resp.reasoning)
        if not sanitized:
            continue

        claims: ExtractedClaims | None = None
        if use_llm and provider is not None:
            claims = await extract_claims_llm(provider, judge_model_id, resp, sanitized, prompt)

        if claims is None:
            claims = extract_claims_heuristic(resp, sanitized, prompt)
            logger.debug(
                "consulate.claims.heuristic | model=%s | claims=%d",
                resp.model_id,
                len(claims.claims),
            )
        else:
            logger.info(
                "consulate.claims.llm | model=%s | claims=%d",
                resp.model_id,
                len(claims.claims),
            )

        extracted.append(claims)

    return extracted


def _infer_topic(prompt: str, text: str) -> str:
    combined = f"{prompt} {text}".lower()
    if "football" in combined or "soccer" in combined:
        return "football"
    if ("depth" in combined and "breadth" in combined) or "career" in combined:
        return "career"
    if any(w in combined for w in ("venture capital", "raise funding", "vc ", " vc", "startup funding")):
        return "startup_funding"
    if "invest" in combined or "stock" in combined or "portfolio" in combined:
        return "investment"
    return "general"


def _infer_interpretation(topic: str, text: str) -> tuple[str, str]:
    lowered = text.lower()
    american_score = sum(1 for s in _AMERICAN_FOOTBALL_SIGNALS if s in lowered)
    soccer_score = sum(1 for s in _SOCCER_SIGNALS if s in lowered)

    if topic == "football":
        if american_score > soccer_score:
            return "american football", "american_football"
        if soccer_score > 0 or american_score == 0:
            return "association football (soccer)", "soccer"
        return "association football (soccer)", "soccer"

    if topic == "investment":
        if any(
            w in lowered
            for w in ("conservative", "bonds", "preserve", "low risk", "cash reserve", "capital preservation")
        ):
            return "conservative preservation", "conservative_investment"
        if any(
            w in lowered
            for w in ("aggressive", "growth", "crypto", "high risk", "speculative")
        ):
            return "aggressive growth", "aggressive_investment"
        return "general investment guidance", "general_investment"

    if topic == "career":
        return _infer_career_interpretation(lowered)

    if topic == "startup_funding":
        if any(w in lowered for w in ("bootstrap", "avoid vc", "without funding", "dilution", "keep control", "self-fund")):
            return "Avoid VC; preserve control", "anti_vc"
        if any(w in lowered for w in ("raise vc", "venture capital", "seek funding", "investors", "scale fast", "raise a round")):
            return "Raise venture capital for growth", "pro_vc"
        return "Funding strategy depends on context", "context_dependent"

    return "general position", _normalize_position_key(text[:120])


def _infer_career_interpretation(lowered: str) -> tuple[str, str]:
    context_signals = (
        "depends", "context", "situation", "case by case", "varies", "no single",
        "no one answer", "individual", "it depends", "both have merit", "balanced",
    )
    depth_signals = (
        "prioritize depth", "depth over breadth", "depth first", "specializ",
        "deep expertise", "mastery", "narrow focus", "go deep", "expertise first",
    )
    breadth_signals = (
        "prioritize breadth", "breadth over depth", "breadth first", "generalist",
        "explore", "wide range", "versatile", "sample", "try many",
    )

    context_score = sum(1 for s in context_signals if s in lowered)
    depth_score = sum(1 for s in depth_signals if s in lowered)
    breadth_score = sum(1 for s in breadth_signals if s in lowered)

    if context_score > 0 and context_score >= depth_score and context_score >= breadth_score:
        return "Context-dependent career approach", "context_dependent"
    if depth_score > breadth_score or ("depth" in lowered and "breadth" not in lowered):
        return "Prioritize depth early in career", "depth_first"
    if breadth_score > depth_score or ("breadth" in lowered and "depth" not in lowered):
        return "Prioritize breadth early in career", "breadth_first"
    return "Balance depth and breadth in career", "balanced_career"


def _extract_factual_claims(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    claims: list[str] = []
    for sentence in sentences:
        s = sentence.strip()
        if len(s) < 20:
            continue
        if re.match(r"^(the user|we need|let me|i will)\b", s, re.I):
            continue
        claims.append(s)
    return claims[:8]


def _build_position_summary(interpretation: str, claims: list[str], text: str) -> str:
    if interpretation and interpretation not in ("general position", "general"):
        return f"Interprets the topic as {interpretation}."
    if claims:
        return claims[0][:200]
    return text[:200]


def _normalize_position_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return key[:64] or "general"


def _parse_json_block(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None
