from agno_v2.vectordb.mongodb.mongodb import MongoDb

# Alias to avoid name collision with the main MongoDb class
MongoVectorDb = MongoDb

__all__ = [
    "MongoVectorDb",
    "MongoDb",
]
