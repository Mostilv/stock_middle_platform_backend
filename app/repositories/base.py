"""
Shared base helpers for repository classes.
"""

from app.db import mongodb


class BaseRepository:
    """Provide access to a MongoDB collection by name."""

    collection_name: str

    def __init__(self) -> None:
        if not hasattr(self, "collection_name"):
            raise ValueError("Repository subclasses must define collection_name")
        self.collection = mongodb.db[self.collection_name]
