from __future__ import annotations

from typing import List, Optional, Union

import tiktoken

from agno.models.message import Message
from agno.session.agent import AgentSession
from agno.session.team import TeamSession
from agno.utils.log import log_debug
from agno.utils.message import get_text_from_message


def _count_tokens_with_encoding(messages: List[Message], model_encoding: str) -> int:
    encoding = tiktoken.get_encoding(model_encoding)
    total_tokens = 0
    for message in messages:
        text = get_text_from_message(message) or ""
        total_tokens += len(encoding.encode(text))
    return total_tokens


def get_messages_within_token_budget(
    session: Union[AgentSession, TeamSession],
    max_tokens: int,
    agent_id: Optional[str] = None,
    team_id: Optional[str] = None,
    skip_roles: Optional[List[str]] = None,
    skip_role: Optional[str] = None,
    model_encoding: str = "cl100k_base",
) -> List[Message]:
    """Fetch the most recent runs' messages that fit within a token budget.

    Called from ``Session.get_messages(max_tokens=...)`` and
    ``Session.get_chat_history(max_tokens=...)``. Iterates from the most recent
    run backward, accumulating whole runs until adding the next run would exceed
    ``max_tokens``. Only a single system message is included overall.

    Args:
        session: The session to get messages from.
        max_tokens: Maximum number of tokens to include from history.
        agent_id: Optional agent id to filter runs.
        team_id: Optional team id to filter runs.
        skip_roles: Skip messages with these roles.
        skip_role: Deprecated alias for a single role to skip.
        model_encoding: The tokenizer encoding to use for token counting.

    Returns:
        A list of `Message` objects, ordered chronologically, whose total
        token content does not exceed `max_tokens`.
    """
    if skip_roles is None and skip_role is not None:
        skip_roles = [skip_role]
    if not session.runs or max_tokens <= 0:
        return []

    session_runs = session.runs
    if agent_id:
        session_runs = [run for run in session_runs if hasattr(run, "agent_id") and run.agent_id == agent_id]  # type: ignore
    if team_id:
        session_runs = [run for run in session_runs if hasattr(run, "team_id") and run.team_id == team_id]  # type: ignore

    total_tokens = 0
    system_added = False
    selected_runs_messages: List[List[Message]] = []

    for run_response in reversed(session_runs):
        if not (run_response and run_response.messages):
            continue

        filtered_messages: List[Message] = []
        system_in_this_run: Optional[Message] = None

        for message in run_response.messages:
            if skip_roles and message.role in skip_roles:
                continue
            if hasattr(message, "from_history") and message.from_history:
                continue

            if message.role == "system":
                if not system_added and system_in_this_run is None:
                    system_in_this_run = message
                continue
            else:
                filtered_messages.append(message)

        if system_in_this_run and not system_added:
            candidate_messages = [system_in_this_run] + filtered_messages
        else:
            candidate_messages = filtered_messages

        if not candidate_messages:
            continue

        run_tokens = _count_tokens_with_encoding(candidate_messages, model_encoding=model_encoding)

        if total_tokens + run_tokens <= max_tokens:
            selected_runs_messages.append(candidate_messages)
            total_tokens += run_tokens
            if system_in_this_run and not system_added:
                system_added = True

    messages_from_history: List[Message] = []
    for msgs in reversed(selected_runs_messages):
        messages_from_history.extend(msgs)

    runs_included = len(selected_runs_messages)
    log_debug(
        f"Getting messages from history with max token budget {max_tokens}: included {runs_included}/{len(session_runs)} whole runs, selected {len(messages_from_history)} messages, tokens used ~{total_tokens}"
    )
    return messages_from_history
