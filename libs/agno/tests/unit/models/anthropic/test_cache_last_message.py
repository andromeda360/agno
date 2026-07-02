"""Tests for cache_last_message on Anthropic Claude models."""

import pytest

pytest.importorskip("anthropic")

from agno.models.anthropic.claude import Claude as AnthropicClaude
from agno.models.message import Message


def _sample_chat_messages():
    return [
        {"role": "user", "content": [{"type": "text", "text": "Hello"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi there"}]},
        {"role": "user", "content": [{"type": "text", "text": "What is 2+2?"}]},
    ]


class TestCacheLastMessage:
    def test_adds_cache_control_to_last_user_block(self):
        model = AnthropicClaude(id="claude-sonnet-4-5-20250929", cache_last_message=True)
        chat_messages = _sample_chat_messages()

        model._apply_cache_control_to_last_user_message(chat_messages)

        last_user = chat_messages[-1]
        assert last_user["role"] == "user"
        assert last_user["content"][-1]["cache_control"] == {"type": "ephemeral"}
        assert "cache_control" not in chat_messages[0]["content"][-1]

    def test_no_cache_when_flag_false(self):
        model = AnthropicClaude(id="claude-sonnet-4-5-20250929", cache_last_message=False)
        chat_messages = _sample_chat_messages()

        model._apply_cache_control_to_last_user_message(chat_messages)

        assert "cache_control" not in chat_messages[-1]["content"][-1]

    def test_extended_cache_time_adds_ttl(self):
        model = AnthropicClaude(
            id="claude-sonnet-4-5-20250929",
            cache_last_message=True,
            extended_cache_time=True,
        )
        chat_messages = _sample_chat_messages()

        model._apply_cache_control_to_last_user_message(chat_messages)

        assert chat_messages[-1]["content"][-1]["cache_control"] == {
            "type": "ephemeral",
            "ttl": "1h",
        }

    def test_tags_last_user_not_last_assistant(self):
        model = AnthropicClaude(id="claude-sonnet-4-5-20250929", cache_last_message=True)
        chat_messages = [
            {"role": "user", "content": [{"type": "text", "text": "First"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Reply"}]},
        ]

        model._apply_cache_control_to_last_user_message(chat_messages)

        assert chat_messages[0]["content"][-1]["cache_control"] == {"type": "ephemeral"}
        assert "cache_control" not in chat_messages[1]["content"][-1]

    def test_append_trailing_user_message_before_cache_tag(self):
        from agno.utils.models.claude import format_messages

        model = AnthropicClaude(
            id="claude-sonnet-4-5-20250929",
            cache_last_message=True,
            append_trailing_user_message=True,
            trailing_user_message_content="continue",
        )
        messages = [
            Message(role="user", content="Classify this ticket"),
            Message(role="assistant", content='{"priority":'),
        ]
        chat_messages, _ = format_messages(
            messages,
            append_trailing_user_message=model.append_trailing_user_message,
            trailing_user_message_content=model.trailing_user_message_content,
        )

        model._apply_cache_control_to_last_user_message(chat_messages)

        assert chat_messages[-1]["role"] == "user"
        assert chat_messages[-1]["content"][-1]["cache_control"] == {"type": "ephemeral"}


def test_aws_claude_thinking_auto_bumps_max_tokens():
    pytest.importorskip("boto3")
    from agno.models.aws.claude import Claude as AwsClaude

    model = AwsClaude(thinking={"type": "enabled", "budget_tokens": 10000})

    request_params = model.get_request_params()

    assert request_params["max_tokens"] == 64000
    assert request_params["thinking"] == {"type": "enabled", "budget_tokens": 10000}
