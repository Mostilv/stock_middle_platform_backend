from typing import Dict

from app.db import db_manager


class BaseCollectionService:
    def __init__(self, collection_name: str) -> None:
        self.collection = db_manager.get_mongodb_collection(collection_name)

    @staticmethod
    def strip_id(document: Dict) -> Dict:
        data = dict(document or {})
        data.pop("_id", None)
        return data
