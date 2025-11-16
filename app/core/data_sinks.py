from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from app.config import settings
from app.db import db_manager


@dataclass(frozen=True)
class DataSink:
    dataset: str
    target: str
    database: str
    collection: str
    description: str = ""


class DataSinkRegistry:
    """Registry describing where different datasets should be persisted."""

    def __init__(self, mapping: Dict[str, Dict[str, Dict[str, str]]]) -> None:
        self._mapping = mapping or {}

    def list_datasets(self) -> Dict[str, List[DataSink]]:
        return {
            dataset: [
                DataSink(
                    dataset=dataset,
                    target=target,
                    database=cfg.get("database") or settings.mongodb_db,
                    collection=cfg.get("collection") or dataset,
                    description=cfg.get("description", ""),
                )
                for target, cfg in targets.items()
            ]
            for dataset, targets in self._mapping.items()
        }

    def resolve(self, dataset: str, target: Optional[str] = None) -> DataSink:
        dataset_key = dataset or ""
        targets = self._mapping.get(dataset_key)
        if not targets:
            raise ValueError(f"未定义的数据集: {dataset_key}")

        target_key = target or next(iter(targets.keys()))
        cfg = targets.get(target_key)
        if not cfg:
            available = ", ".join(targets.keys())
            raise ValueError(
                f"数据集 {dataset_key} 不存在目标 {target_key}。可选: {available}"
            )

        database = cfg.get("database") or settings.mongodb_db
        collection = cfg.get("collection") or dataset_key
        if not collection:
            raise ValueError(f"数据集 {dataset_key} 的 collection 未配置")

        return DataSink(
            dataset=dataset_key,
            target=target_key,
            database=database,
            collection=collection,
            description=cfg.get("description", ""),
        )

    def get_collection(self, dataset: str, target: Optional[str] = None):
        sink = self.resolve(dataset, target)
        database = db_manager.get_database(sink.database)
        return database[sink.collection]

    def describe(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            dataset: [
                {
                    "target": sink.target,
                    "database": sink.database,
                    "collection": sink.collection,
                    "description": sink.description,
                }
                for sink in sinks
            ]
            for dataset, sinks in self.list_datasets().items()
        }


data_sink_registry = DataSinkRegistry(settings.data_targets)
