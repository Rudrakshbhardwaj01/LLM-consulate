"""LLM-based second-pass agreement judge."""

import json
import re
import time

from app.orchestrator.consensus.majority_vote import analyze_majority
from app.orchestrator.consensus.models import ExtractedClaims, JudgeVerdict, PositionCluster
from app.providers.nvidia_provider import NvidiaProvider
from app.orchestrator.synthesis_prompt import truncate_text
from app.schemas.chat import ChatMessage
from app.utils.logging import get_logger

logger = get_logger(__name__)

JUDGE_SYSTEM_PROMPT = """You are the Agreement Judge for LLM Consulate.

Given multiple council responses to the same user question, determine whether they fundamentally agree on meaning.

IGNORE completely:
- writing style
- formatting differences
- verbosity differences
- tone differences

Focus ONLY on:
- primary interpretation
- factual claims
- recommendations and conclusions

Return ONLY valid JSON:
{
  "fundamentally_agree": true or false,
  "majority_position": "one sentence",
  "minority_positions": ["optional minority views"],
  "confidence": 0.0 to 1.0,
  "disputed_concept": "what concept is disputed, if any",
  "explanation": "brief explanation"
}"""


async def run_judge(
    provider: NvidiaProvider | None,
    judge_model_id: str,
    prompt: str,
    claims: list[ExtractedClaims],
    clusters: list[PositionCluster],
    use_llm: bool = True,
) -> JudgeVerdict:
    """Run LLM judge or fall back to majority-vote heuristic."""
    start = time.perf_counter()
    majority, minority, maj_support, min_support, is_deadlock, _outcome, disagreement = (
        analyze_majority(clusters, prompt=prompt, topic=claims[0].topic if claims else "")
    )

    heuristic = JudgeVerdict(
        fundamentally_agree=not is_deadlock,
        majority_position=majority.position_label if majority else "",
        minority_positions=[minority.position_label] if minority else [],
        confidence=maj_support if majority else 0.0,
        disputed_concept=disagreement.disputed_concept if disagreement else "",
        explanation=disagreement.explanation if disagreement else "",
        source="heuristic",
    )

    if not use_llm or provider is None or not provider.is_configured():
        judge_ms = int((time.perf_counter() - start) * 1000)
        logger.info("consulate.judge | source=heuristic | confidence=%.3f", heuristic.confidence)
        logger.info("consulate.timing | stage=judge | source=heuristic | judge_ms=%d", judge_ms)
        return heuristic

    responses_block = []
    for c in claims:
        responses_block.append(
            f"--- {c.model_name} ({c.model_id}) ---\n"
            f"Interpretation: {c.interpretation}\n"
            f"Position: {c.position_summary}\n"
            f"Claims: {'; '.join(c.claims[:5])}\n"
            f"Response excerpt: {c.sanitized_text[:500]}"
        )

    user_content = (
        f"User question:\n{truncate_text(prompt, 1500)}\n\n"
        f"Council responses ({len(claims)} members):\n\n"
        f"{chr(10).join(responses_block)}"
    )

    messages = [
        ChatMessage.create("system", JUDGE_SYSTEM_PROMPT),
        ChatMessage.create("user", user_content),
    ]

    try:
        result = await provider.invoke(judge_model_id, messages)
        if not result.success or not result.effective_content:
            logger.warning("consulate.judge | llm_empty | falling back to heuristic")
            return heuristic

        parsed = _parse_json_block(result.effective_content)
        if not parsed:
            logger.warning("consulate.judge | llm_parse_failed | falling back to heuristic")
            return heuristic

        verdict = JudgeVerdict(
            fundamentally_agree=bool(parsed.get("fundamentally_agree", not is_deadlock)),
            majority_position=str(parsed.get("majority_position", heuristic.majority_position)),
            minority_positions=[
                str(p) for p in parsed.get("minority_positions", []) if str(p).strip()
            ],
            confidence=float(parsed.get("confidence", heuristic.confidence)),
            disputed_concept=str(parsed.get("disputed_concept", heuristic.disputed_concept)),
            explanation=str(parsed.get("explanation", heuristic.explanation)),
            source="llm",
        )
        judge_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "consulate.judge | source=llm | agree=%s | confidence=%.3f",
            verdict.fundamentally_agree,
            verdict.confidence,
        )
        logger.info("consulate.timing | stage=judge | source=llm | judge_ms=%d", judge_ms)
        return verdict

    except Exception as exc:
        judge_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("consulate.judge | llm_failed | error=%s", exc)
        logger.info("consulate.timing | stage=judge | source=heuristic_fallback | judge_ms=%d", judge_ms)
        return heuristic


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
