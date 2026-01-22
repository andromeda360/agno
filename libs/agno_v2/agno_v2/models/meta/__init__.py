from agno_v2.models.meta.llama import Llama

try:
    from agno_v2.models.meta.llama_openai import LlamaOpenAI
except ImportError:

    class LlamaOpenAI:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("`openai` not installed. Please install it via `pip install openai`")


__all__ = ["Llama", "LlamaOpenAI"]
