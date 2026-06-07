"""Tests for ChatMessage length guards and message_guard utilities."""

import pytest

from app.orchestrator.message_guard import assert_messages_within_limit, ensure_message_list
from app.orchestrator.synthesis_prompt import build_deadlock_user_content
from app.orchestrator.consensus.models import ConsensusResult, ExtractedClaims, PositionCluster
from app.schemas.chat import MAX_MESSAGE_CHARS, ChatMessage
from app.schemas.provider import ModelResponse


def test_chat_message_auto_truncates_on_construction():
    oversized = "x" * 16_179
    message = ChatMessage(role="user", content=oversized)
    assert len(message.content) <= MAX_MESSAGE_CHARS


def test_chat_message_create_never_raises():
    message = ChatMessage.create("user", "y" * 20_000)
    assert len(message.content) <= MAX_MESSAGE_CHARS


def test_ensure_message_list_truncates_existing_messages():
    messages = [ChatMessage(role="user", content="z" * 15_000)]
    guarded = ensure_message_list(messages)
    assert len(guarded[0].content) <= MAX_MESSAGE_CHARS


def test_assert_messages_within_limit_passes():
    messages = [ChatMessage.create("user", "hello")]
    assert_messages_within_limit(messages)


def test_assert_messages_within_limit_fails():
    message = ChatMessage.model_construct(role="user", content="a" * 20_000)
    with pytest.raises(AssertionError):
        assert_messages_within_limit([message])


def test_deadlock_prompt_never_includes_full_essays():
    long_text = "word " * 4000
    claims = [
        ExtractedClaims(
            modelId="gpt-oss-120b",
            modelName="GPT-OSS 120B",
            positionSummary=long_text,
            claims=[long_text, long_text],
            sanitizedText=long_text,
        ),
        ExtractedClaims(
            modelId="nemotron-omni-30b",
            modelName="Nemotron Omni 30B",
            positionSummary=long_text,
            claims=[long_text],
            sanitizedText=long_text,
        ),
    ]
    consensus = ConsensusResult(
        agreementScore=0.32,
        isDeadlock=True,
        majorityPosition=long_text,
        minorityPosition=long_text,
        majoritySupport=0.25,
        extractedClaims=claims,
        clusters=[
            PositionCluster(
                positionKey="a",
                positionLabel="A",
                positionSummary=long_text[:200],
                modelIds=["gpt-oss-120b"],
                modelNames=["GPT-OSS 120B"],
                count=1,
                support=0.25,
            )
        ],
    )
    responses = [
        ModelResponse(modelId="gpt-oss-120b", modelName="GPT-OSS 120B", content=long_text, success=True),
        ModelResponse(modelId="nemotron-omni-30b", modelName="Nemotron Omni 30B", content=long_text, success=True),
    ]

    user_content, _meta = build_deadlock_user_content("Question", consensus, responses)
    assert len(user_content) <= MAX_MESSAGE_CHARS
    assert long_text[:500] not in user_content

    messages = [
        ChatMessage.create("system", "system"),
        ChatMessage.create("user", user_content),
    ]
    assert_messages_within_limit(messages)
