from agno.models.google.gemini import Gemini

__all__ = [
    "Gemini",
    "GeminiInteractions",
]


def __getattr__(name: str):
    if name == "GeminiInteractions":
        from agno.models.google.gemini_interactions import GeminiInteractions

        return GeminiInteractions
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
