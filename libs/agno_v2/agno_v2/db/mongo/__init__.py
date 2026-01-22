from typing import TYPE_CHECKING

from agno_v2.db.mongo.mongo import MongoDb

if TYPE_CHECKING:
    from agno_v2.db.mongo.async_mongo import AsyncMongoDb

__all__ = ["AsyncMongoDb", "MongoDb"]


def __getattr__(name: str):
    """Lazy import AsyncMongoDb only when accessed."""
    if name == "AsyncMongoDb":
        from agno_v2.db.mongo.async_mongo import AsyncMongoDb

        return AsyncMongoDb
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
