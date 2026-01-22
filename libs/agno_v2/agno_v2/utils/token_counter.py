"""
Token counting utility using tiktoken.

This is a custom Andromeda360 feature that provides token counting
without external dependencies on banavo.utils.token_counter.
"""

from typing import List, Union

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore


def count_tokens(
    messages: Union[str, List, dict],
    model: str = "gpt-4",
) -> int:
    """
    Count tokens in messages using tiktoken.

    Args:
        messages: String, list of messages, or dict to count tokens for
        model: Model name to use for token encoding (default: gpt-4)

    Returns:
        int: Number of tokens

    Raises:
        ImportError: If tiktoken is not installed
    """
    if tiktoken is None:
        raise ImportError(
            "tiktoken is required for token counting. "
            "Install it with: pip install tiktoken"
        )

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base encoding (used by GPT-4)
        encoding = tiktoken.get_encoding("cl100k_base")

    # Handle string input
    if isinstance(messages, str):
        return len(encoding.encode(messages))

    # Handle dict input
    if isinstance(messages, dict):
        text = str(messages)
        return len(encoding.encode(text))

    # Handle list of messages
    if isinstance(messages, list):
        num_tokens = 0
        for message in messages:
            if isinstance(message, dict):
                # Count tokens for each key-value pair
                for key, value in message.items():
                    num_tokens += len(encoding.encode(str(value)))
            elif isinstance(message, str):
                num_tokens += len(encoding.encode(message))
            else:
                # Convert to string for other types
                num_tokens += len(encoding.encode(str(message)))

        return num_tokens

    # Fallback: convert to string
    return len(encoding.encode(str(messages)))
