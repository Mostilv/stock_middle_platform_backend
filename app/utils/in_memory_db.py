import asyncio
import copy
from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId


def _matches(document: Dict[str, Any], filter_query: Dict[str, Any]) -> bool:
    if not filter_query:
        return True

    for field, expected in filter_query.items():
        if isinstance(expected, dict):
            if "$in" in expected:
                if document.get(field) not in expected["$in"]:
                    return False
            else:
                if document.get(field) != expected:
                    return False
        else:
            if document.get(field) != expected:
                return False
    return True


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, modified_count: int) -> None:
        self.modified_count = modified_count


class DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class InMemoryCursor:
    def __init__(self, collection: "InMemoryCollection", filter_query: Dict[str, Any]) -> None:
        self._collection = collection
        self._filter = filter_query or {}
        self._skip = 0
        self._limit: Optional[int] = None
        self._sort: Optional[tuple[str, int]] = None
        self._iter: Optional[Iterable[Dict[str, Any]]] = None

    def skip(self, count: int) -> "InMemoryCursor":
        self._skip = max(count, 0)
        return self

    def limit(self, count: int) -> "InMemoryCursor":
        self._limit = max(count, 0)
        return self

    def sort(self, key: str, direction: int) -> "InMemoryCursor":
        self._sort = (key, direction)
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = length if length is not None else self._limit
        results = self._prepare_results(limit)
        await asyncio.sleep(0)
        return results

    def __aiter__(self) -> "InMemoryCursor":
        self._iter = iter(self._prepare_results(self._limit))
        return self

    async def __anext__(self) -> Dict[str, Any]:
        if self._iter is None:
            self._iter = iter(self._prepare_results(self._limit))
        try:
            item = next(self._iter)
        except StopIteration as exc:  # pragma: no cover - defensive
            raise StopAsyncIteration from exc
        await asyncio.sleep(0)
        return item

    def _prepare_results(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        documents = [
            self._collection._clone_document(document)
            for document in self._collection._documents
            if _matches(document, self._filter)
        ]

        if self._sort:
            key, direction = self._sort
            reverse = direction < 0
            documents.sort(key=lambda item: item.get(key), reverse=reverse)

        if self._skip:
            documents = documents[self._skip :]

        if limit is not None:
            documents = documents[:limit]

        return documents


class InMemoryCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self._documents: List[Dict[str, Any]] = []

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for document in self._documents:
            if _matches(document, filter_query):
                await asyncio.sleep(0)
                return self._clone_document(document)
        await asyncio.sleep(0)
        return None

    async def insert_one(self, document: Dict[str, Any]) -> InsertOneResult:
        new_document = self._clone_document(document)
        if "_id" not in new_document:
            new_document["_id"] = ObjectId()
        elif isinstance(new_document["_id"], str):
            new_document["_id"] = ObjectId(new_document["_id"])
        self._documents.append(new_document)
        await asyncio.sleep(0)
        return InsertOneResult(new_document["_id"])

    async def update_one(self, filter_query: Dict[str, Any], update_doc: Dict[str, Any]) -> UpdateResult:
        modified_count = 0
        for document in self._documents:
            if not _matches(document, filter_query):
                continue

            updated = False

            if "$set" in update_doc:
                for field, value in update_doc["$set"].items():
                    document[field] = value
                    updated = True

            if "$addToSet" in update_doc:
                for field, payload in update_doc["$addToSet"].items():
                    values: Iterable[Any]
                    if isinstance(payload, dict) and "$each" in payload:
                        values = payload["$each"]
                    else:
                        values = [payload]
                    current_values = document.setdefault(field, [])
                    for item in values:
                        if item not in current_values:
                            current_values.append(item)
                            updated = True

            if "$pull" in update_doc:
                for field, payload in update_doc["$pull"].items():
                    if isinstance(payload, dict) and "$in" in payload:
                        values = set(payload["$in"])
                        current_values = document.get(field, [])
                        if isinstance(current_values, list):
                            original_length = len(current_values)
                            document[field] = [item for item in current_values if item not in values]
                            if len(document[field]) != original_length:
                                updated = True
                    else:
                        current_values = document.get(field, [])
                        if isinstance(current_values, list) and payload in current_values:
                            current_values.remove(payload)
                            updated = True

            if updated:
                modified_count += 1
                break

        await asyncio.sleep(0)
        return UpdateResult(modified_count)

    async def delete_one(self, filter_query: Dict[str, Any]) -> DeleteResult:
        for index, document in enumerate(self._documents):
            if _matches(document, filter_query):
                del self._documents[index]
                await asyncio.sleep(0)
                return DeleteResult(1)
        await asyncio.sleep(0)
        return DeleteResult(0)

    def find(self, filter_query: Optional[Dict[str, Any]] = None) -> InMemoryCursor:
        return InMemoryCursor(self, filter_query or {})

    def _clone_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        return copy.deepcopy(document)


class InMemoryDatabase:
    def __init__(self) -> None:
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]

    def list_collection_names(self) -> List[str]:
        return list(self._collections.keys())

    def reset(self) -> None:
        self._collections.clear()
