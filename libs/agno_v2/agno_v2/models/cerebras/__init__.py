from agno_v2.models.cerebras.cerebras import Cerebras

try:
    from agno_v2.models.cerebras.cerebras_openai import CerebrasOpenAI
except ImportError:

    class CerebrasOpenAI:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("`openai` not installed. Please install it via `pip install openai`")


__all__ = ["Cerebras", "CerebrasOpenAI"]
