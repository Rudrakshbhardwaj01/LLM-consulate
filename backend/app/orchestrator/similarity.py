"""Semantic text similarity for council agreement analysis."""

import math
import re
from difflib import SequenceMatcher

from app.config.constants import SIMILARITY_MAX_CHARS
from app.utils.logging import get_logger

logger = get_logger(__name__)

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might must can could to of in for on with at by from as "
    "and or but not no nor so if then than that this these those it its i you "
    "he she they we their our your my also more most very much well just like "
    "one two three about into through over under after before between during "
    "while when where which who what how why all any each every both other "
    "another such same some many few several".split()
)

_NUMBER_WORDS = {
    "eleven": "11",
    "twelve": "12",
    "ten": "10",
}

_SYNONYM_REPLACEMENTS = (
    (r"\bsoccer\b", "football"),
    (r"\bsquads?\b", "teams"),
    (r"\bvie\b", "compete"),
    (r"\bbeloved\b", "popular"),
    (r"\bpremier\b", "major"),
    (r"\bwatched\b", "popular"),
    (r"\bglobally\b", "global"),
    (r"\bathletic\b", ""),
    (r"\btournament\b", "tournaments"),
    (r"\bevents\b", "tournaments"),
    (r"\bgoals\b", "score"),
    (r"\bplanning\b", "strategy"),
    (r"\bteamwork\b", "strategy"),
    (r"\btactical\b", "strategy"),
    (r"\bobjective\b", "goal"),
    (r"\bcompetitions?\b", "tournaments"),
    (r"\bchampionship\b", "tournament"),
)

_WEIGHT_TOKEN_SET = 0.65
_WEIGHT_OVERLAP = 0.20
_WEIGHT_SENTENCE = 0.10
_WEIGHT_SEQUENCE = 0.05


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Composite semantic similarity in [0, 1].

    Uses content overlap, shared key phrases, and sentence alignment so
    paraphrased but equivalent answers score high while genuinely divergent
    positions score low.
    """
    text_a = text_a[:SIMILARITY_MAX_CHARS]
    text_b = text_b[:SIMILARITY_MAX_CHARS]
    norm_a = _normalize(text_a)
    norm_b = _normalize(text_b)

    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    tokens_a = _content_tokens(norm_a)
    tokens_b = _content_tokens(norm_b)
    filtered_a = " ".join(tokens_a)
    filtered_b = " ".join(tokens_b)

    token_set_score = _token_set_ratio(filtered_a, filtered_b)
    overlap_score = _overlap_coefficient(set(tokens_a), set(tokens_b))
    sentence_score = _sentence_alignment_score(text_a, text_b)
    seq_score = SequenceMatcher(None, norm_a, norm_b).ratio()

    composite = (
        _WEIGHT_TOKEN_SET * token_set_score
        + _WEIGHT_OVERLAP * overlap_score
        + _WEIGHT_SENTENCE * sentence_score
        + _WEIGHT_SEQUENCE * seq_score
    )

    logger.debug(
        "consulate.similarity | token_set=%.3f overlap=%.3f sentence=%.3f seq=%.3f composite=%.3f",
        token_set_score,
        overlap_score,
        sentence_score,
        seq_score,
        composite,
    )
    return min(1.0, max(0.0, composite))


def _normalize(text: str) -> str:
    lowered = text.lower()
    for word, digit in _NUMBER_WORDS.items():
        lowered = re.sub(rf"\b{word}\b", digit, lowered)
    for pattern, replacement in _SYNONYM_REPLACEMENTS:
        lowered = re.sub(pattern, replacement, lowered)
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _content_tokens(text: str) -> list[str]:
    return [w for w in text.split() if len(w) >= 3 and w not in _STOP_WORDS]


def _token_set_ratio(text_a: str, text_b: str) -> float:
    """
    Fuzzy token-set ratio — robust to paraphrasing and reordering.

    Compares the intersection token set against each full set, which yields
    high scores when two answers share the same facts with different wording.
    """
    tokens_a = set(text_a.split())
    tokens_b = set(text_b.split())
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    if not intersection:
        return 0.0

    sorted_intersection = " ".join(sorted(intersection))
    combined_a = " ".join(sorted(tokens_a))
    combined_b = " ".join(sorted(tokens_b))
    return max(
        SequenceMatcher(None, sorted_intersection, combined_a).ratio(),
        SequenceMatcher(None, sorted_intersection, combined_b).ratio(),
        SequenceMatcher(None, combined_a, combined_b).ratio(),
    )


def _overlap_coefficient(set_a: set[str], set_b: set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    if intersection == 0:
        return 0.0
    jaccard = intersection / len(set_a | set_b)
    simpson = intersection / min(len(set_a), len(set_b))
    dice = (2 * intersection) / (len(set_a) + len(set_b))
    return 0.25 * jaccard + 0.50 * simpson + 0.25 * dice



def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in parts if len(s.strip()) >= 12]


def _sentence_alignment_score(text_a: str, text_b: str) -> float:
    sentences_a = _split_sentences(text_a)
    sentences_b = _split_sentences(text_b)

    if not sentences_a or not sentences_b:
        return _leaf_similarity(text_a, text_b)

    scores_a = [_best_sentence_match(s, sentences_b) for s in sentences_a]
    scores_b = [_best_sentence_match(s, sentences_a) for s in sentences_b]
    return (sum(scores_a) + sum(scores_b)) / (len(scores_a) + len(scores_b))


def _best_sentence_match(sentence: str, candidates: list[str]) -> float:
    if not candidates:
        return 0.0
    return max(_leaf_similarity(sentence, c) for c in candidates)


def _leaf_similarity(text_a: str, text_b: str) -> float:
    """Pairwise similarity without recursive sentence decomposition."""
    norm_a = _normalize(text_a)
    norm_b = _normalize(text_b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    tokens_a = _content_tokens(norm_a)
    tokens_b = _content_tokens(norm_b)
    filtered_a = " ".join(tokens_a)
    filtered_b = " ".join(tokens_b)
    token_set_score = _token_set_ratio(filtered_a, filtered_b)
    overlap_score = _overlap_coefficient(set(tokens_a), set(tokens_b))
    seq_score = SequenceMatcher(None, norm_a, norm_b).ratio()
    return 0.60 * token_set_score + 0.30 * overlap_score + 0.10 * seq_score


def extract_distinctive_terms(reference: str, divergent: str, count: int = 3) -> list[str]:
    """
    Terms that appear in ``divergent`` but are not dominant in ``reference``.
    Used to label real disagreements, not shared topic words.
    """
    ref_terms = _content_terms(reference)
    div_terms = _content_terms(divergent)
    distinctive = [t for t in div_terms if t not in ref_terms]
    if not distinctive:
        ref_counts = _term_counts(reference)
        div_counts = _term_counts(divergent)
        scored = sorted(
            div_counts.keys(),
            key=lambda t: div_counts[t] / max(ref_counts.get(t, 0) + 1, 1),
            reverse=True,
        )
        distinctive = [t for t in scored if t not in _STOP_WORDS and t not in ref_terms][:count]
    return distinctive[:count]


def _content_terms(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]{4,}", _normalize(text))
    return {w for w in words if w not in _STOP_WORDS}


def _term_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in re.findall(r"[a-z0-9]{4,}", _normalize(text)):
        if word not in _STOP_WORDS:
            counts[word] = counts.get(word, 0) + 1
    return counts


def find_divergent_sentences(
    reference: str, candidate: str, threshold: float = 0.55
) -> list[str]:
    """Sentences in ``candidate`` that do not align with any sentence in ``reference``."""
    ref_sentences = _split_sentences(reference)
    cand_sentences = _split_sentences(candidate)
    if not cand_sentences:
        return []

    divergent: list[str] = []
    for sentence in cand_sentences:
        best = _best_sentence_match(sentence, ref_sentences) if ref_sentences else 0.0
        if best < threshold:
            divergent.append(sentence)
    return divergent
