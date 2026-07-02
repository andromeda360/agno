"""Banavo stream event marker for Agno tool-generator and response-chunk handling."""

from typing import ClassVar


class BaseBanavoStreamEvent:
    """Marker base for Banavo typed SSE events (UI, metadata, agent observability).

    Subclass from banavo ``StreamEventBase`` (or this class directly). Agno checks
    ``isinstance(event, BaseBanavoStreamEvent)`` to stream UI payloads without
    accumulating ``str(item)`` into ``tool.result`` or treating them as ``ModelResponse``.
    """

    _streaming_only: ClassVar[bool] = True
