"""
Shared base helpers for repository classes.
"""

from typing import Any, Optional

from app.db import db_manager, mongodb


class BaseRepository:
    """Provide access to a MongoDB collection by name."""

    collection_name: str

    def __init__(
        self,
        *,
        collection: Optional[Any] = None,
        database_name: Optional[str] = None,
    ) -> None:
        if not hasattr(self, "collection_name"):
            raise ValueError("Repository subclasses must define collection_name")

        if collection is not None:
            self.collection = collection
        elif database_name:
            self.collection = db_manager.get_database(database_name)[self.collection_name]
        else:
            self.collection = mongodb.db[self.collection_name]
