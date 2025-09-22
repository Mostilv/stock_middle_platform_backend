from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class InMemoryCursor:
    def __init__(self, documents: List[Dict[str, Any]]) -> None:
        self._documents = documents
        self._index = 0

    def __aiter__(self) -> "InMemoryCursor":
        return self

    async def __anext__(self) -> Dict[str, Any]:
        if self._index >= len(self._documents):
            raise StopAsyncIteration
        doc = self._documents[self._index]
        self._index += 1
        return doc


class InMemoryCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self._documents: List[Dict[str, Any]] = []

    async def insert_many(self, docs: Iterable[Dict[str, Any]]) -> None:
        for doc in docs:
            self._documents.append(dict(doc))

    async def replace_one(self, filter: Dict[str, Any], doc: Dict[str, Any], upsert: bool = False) -> None:
        for idx, existing in enumerate(self._documents):
            if all(existing.get(k) == v for k, v in filter.items()):
                self._documents[idx] = dict(doc)
                return
        if upsert:
            self._documents.append(dict(doc))

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> None:
        for existing in self._documents:
            if all(existing.get(k) == v for k, v in filter.items()):
                if "$set" in update:
                    existing.update(update["$set"])
                return
        if upsert:
            doc = dict(filter)
            if "$set" in update:
                doc.update(update["$set"])
            self._documents.append(doc)

    async def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self._documents:
            if all(doc.get(k) == v for k, v in filter.items()):
                return dict(doc)
        return None

    async def find(self, filter: Dict[str, Any]) -> InMemoryCursor:
        docs = [doc for doc in self._documents if all(doc.get(k) == v for k, v in filter.items())]
        return InMemoryCursor([dict(doc) for doc in docs])

    async def create_index(self, spec: Iterable[tuple[str, int]], unique: bool = False) -> None:  # pragma: no cover
        return None


class InMemoryDatabase:
    def __init__(self) -> None:
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]


_DATABASE = InMemoryDatabase()


def get_database() -> InMemoryDatabase:
    return _DATABASE


async def close_database() -> None:  # pragma: no cover
    return None


__all__ = ["get_database", "close_database", "InMemoryCollection"]
