"""Extract structured claims and interpretations from council responses."""

import asyncio
import json
import re
import time

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

_APARTMENT_FRIENDLY_BREEDS = (
    "shiba inu",
    "shiba",
    "toy poodle",
    "miniature poodle",
    "poodle",
    "french bulldog",
    "frenchie",
    "cavalier king charles spaniel",
    "cavalier king charles",
    "cavalier",
)

# Longest phrases first so "shiba inu" wins over "shiba".
_PET_RECOMMENDATION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("cavalier king charles spaniel", "cavalier_king_charles_spaniel"),
    ("cavalier king charles", "cavalier_king_charles_spaniel"),
    ("siberian husky", "siberian_husky"),
    ("shiba inu", "shiba_inu"),
    ("toy poodle", "toy_poodle"),
    ("miniature poodle", "toy_poodle"),
    ("french bulldog", "french_bulldog"),
    ("shih tzu", "shih_tzu"),
    ("pomeranian", "pomeranian"),
    ("maltese", "maltese"),
    ("shiba", "shiba_inu"),
    ("poodle", "toy_poodle"),
    ("frenchie", "french_bulldog"),
    ("cavalier", "cavalier_king_charles_spaniel"),
    ("husky", "siberian_husky"),
)

_APARTMENT_CONTEXT_SIGNALS = (
    "apartment",
    "small space",
    "small living",
    "compact",
    "urban",
    "tokyo",
    "city",
    "indoors",
    "indoor",
)

_APARTMENT_UNSUITABLE_PATTERNS = (
    re.compile(
        r"not (?:ideal|recommended|suited|suitable|good) (?:\w+ ){0,5}"
        r"for (?:a )?(?:small |tiny |urban )?apartments?"
    ),
    re.compile(
        r"not (?:ideal|recommended|suited|suitable) "
        r"for (?:small |compact |urban )(?:living|spaces?|homes?)"
    ),
    re.compile(
        r"(?:avoid|poor choice|does not work(?: well)?|not suited) "
        r"(?:\w+ ){0,8}(?:for )?(?:a )?(?:small |tiny )?apartments?"
    ),
    re.compile(r"not ideal for small tokyo apartments"),
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
    topic_key = topic
    interpretation, position_key = _infer_interpretation(topic, sanitized)
    primary_recommendation = _extract_primary_recommendation(
        topic_key, sanitized, position_key
    )
    claims = _extract_factual_claims(sanitized)
    position_summary = _build_position_summary(interpretation, claims, sanitized)

    return ExtractedClaims(
        modelId=response.model_id,
        modelName=response.model_name,
        topic=topic,
        topicKey=topic_key,
        interpretation=interpretation,
        positionKey=position_key,
        primaryRecommendation=primary_recommendation,
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

        topic = str(parsed.get("topic", "")).strip() or _infer_topic(prompt, sanitized)
        return ExtractedClaims(
            modelId=response.model_id,
            modelName=response.model_name,
            topic=topic,
            topicKey=topic,
            interpretation=interpretation,
            positionKey=position_key,
            primaryRecommendation=_extract_primary_recommendation(
                topic, sanitized, position_key
            ),
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
    """Extract claims for every successful response (LLM calls run in parallel)."""

    async def _extract_one(resp: ModelResponse) -> ExtractedClaims | None:
        model_start = time.perf_counter()
        sanitized = sanitize_council_content(resp.content, resp.reasoning)
        if not sanitized:
            return None

        claims: ExtractedClaims | None = None
        source = "heuristic"
        if use_llm and provider is not None:
            claims = await extract_claims_llm(provider, judge_model_id, resp, sanitized, prompt)
            if claims is not None:
                source = "llm"

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

        model_ms = int((time.perf_counter() - model_start) * 1000)
        logger.info(
            "consulate.timing | stage=claim_extraction | model=%s | source=%s | ms=%d | position_key=%s",
            resp.model_id,
            source,
            model_ms,
            claims.position_key,
        )
        return claims

    batch_start = time.perf_counter()
    results = await asyncio.gather(*[_extract_one(resp) for resp in responses])
    batch_ms = int((time.perf_counter() - batch_start) * 1000)
    logger.info(
        "consulate.timing | stage=claim_extraction | models=%d | use_llm=%s | claims_ms=%d",
        len(responses),
        use_llm,
        batch_ms,
    )
    return [claim for claim in results if claim is not None]


def _extract_primary_recommendation(
    topic_key: str,
    text: str,
    position_key: str,
) -> str:
    """Specific recommendation slug used for vote support (distinct from position_key)."""
    lowered = text.lower()
    if topic_key == "pets":
        for phrase, key in _PET_RECOMMENDATION_PATTERNS:
            if phrase in lowered:
                return key
        if position_key == "apartment_friendly_pet":
            return "apartment_friendly_general"
        if position_key == "active_pet":
            return "active_pet_general"

    if topic_key == "football" and position_key in {"soccer", "american_football"}:
        return position_key

    if position_key:
        return position_key
    return "general_recommendation"


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
    if any(w in combined for w in ("dog", "breed", "puppy", "pet", "cat")):
        return "pets"
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

    if topic == "pets":
        return _infer_pets_interpretation(lowered)

    return "general position", "general_position"


def _infer_pets_interpretation(lowered: str) -> tuple[str, str]:
    if _is_apartment_unsuitable_recommendation(lowered):
        return "Active/large breed recommendation", "active_pet"

    if _recommends_apartment_friendly_breed(lowered) or _has_positive_apartment_endorsement(lowered):
        return "Apartment-friendly breed recommendation", "apartment_friendly_pet"

    apartment_signals = (
        "apartment", "small space", "small living", "compact", "urban", "tokyo",
        "city", "low maintenance", "small breed", "apartment-friendly",
    )
    active_signals = (
        "high energy", "large breed", "yard", "suburban", "needs space", "working dog",
        "substantial outdoor",
    )
    apartment_score = sum(1 for signal in apartment_signals if signal in lowered)
    active_score = sum(1 for signal in active_signals if signal in lowered)

    if apartment_score > active_score:
        return "Apartment-friendly breed recommendation", "apartment_friendly_pet"
    if active_score > apartment_score:
        return "Active/large breed recommendation", "active_pet"
    return "General pet breed recommendation", "general_recommendation"


def _is_apartment_unsuitable_recommendation(lowered: str) -> bool:
    """True only when the response argues the breed is a poor fit for apartment living."""
    if not any(pattern.search(lowered) for pattern in _APARTMENT_UNSUITABLE_PATTERNS):
        return False
    if _endorses_apartment_living(lowered):
        return False
    return True


def _endorses_apartment_living(lowered: str) -> bool:
    """True when the response ultimately recommends apartment or Tokyo living."""
    has_context = any(signal in lowered for signal in _APARTMENT_CONTEXT_SIGNALS)
    if not has_context:
        return False

    endorsement_patterns = (
        re.compile(r"\b(?:recommend|excellent|best|great|perfect|works well|good choice|top pick)\b"),
        re.compile(r"well[- ]suited"),
        re.compile(r"\bfits\b"),
        re.compile(r"strong fit"),
        re.compile(r"suited to"),
        re.compile(r"(?<!\bnot )\bideal for (?:apartment|tokyo|urban|city|indoor)"),
        re.compile(r"perfect for (?:apartment|urban|city|tokyo|indoor)"),
        re.compile(
            r"(?<!\bnot )(?:excellent|best|great|perfect) (?:\w+ ){0,4}(?:for )?"
            r"(?:tokyo|apartment|urban|city)"
        ),
    )
    return any(pattern.search(lowered) for pattern in endorsement_patterns)


def _has_positive_apartment_endorsement(lowered: str) -> bool:
    return _endorses_apartment_living(lowered)


def _recommends_apartment_friendly_breed(lowered: str) -> bool:
    mentions_breed = any(breed in lowered for breed in _APARTMENT_FRIENDLY_BREEDS)
    if not mentions_breed:
        return False
    negates_breed = any(
        phrase in lowered
        for phrase in ("not recommend", "avoid", "do not get", "don't get", "stay away from")
    )
    return _endorses_apartment_living(lowered) and not negates_breed


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
