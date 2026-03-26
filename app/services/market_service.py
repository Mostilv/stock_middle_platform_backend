from typing import Dict, List, Optional

from app.db import db_manager
from app.models.market import MarketDataResponse
from app.services.collection_service import BaseCollectionService


class MarketDataService(BaseCollectionService):
    DEFAULT_DATA: Dict[str, Dict] = {
        "shanghaiIndex": {
            "current": 3700.25,
            "change": 1.25,
            "history": [3680.5, 3695.2, 3710.8, 3698.45, 3700.25],
        },
        "nasdaqIndex": {
            "current": 16543.67,
            "change": -0.85,
            "history": [16680.3, 16620.15, 16580.9, 16560.25, 16543.67],
        },
        "goldIndex": {
            "current": 2345.89,
            "change": 2.15,
            "history": [2295.6, 2310.25, 2325.8, 2335.45, 2345.89],
        },
        "zhongzheng2000Index": {
            "current": 1245.67,
            "change": 0.75,
            "history": [1235.2, 1240.8, 1242.5, 1243.9, 1245.67],
        },
    }

    def __init__(self) -> None:
        super().__init__("market_data")

    async def get_market_data(
        self,
        symbols: Optional[List[str]],
        history_days: int,
    ) -> MarketDataResponse:
        indices_col = db_manager.get_mongodb_collection("market_indices")
        latest = await indices_col.find_one({"_id": "latest_indices"})

        result: Dict[str, Dict] = {}
        if latest:
            source_data = {key: value for key, value in latest.items() if key != "_id"}
            for symbol, data in source_data.items():
                if symbols and symbol not in symbols:
                    continue
                history = list(data.get("history", []))
                result[symbol] = {
                    "current": float(data.get("current", 0)),
                    "change": float(data.get("change", 0)),
                    "history": history[-history_days:] if history_days else history,
                }

        if symbols:
            for symbol in symbols:
                if symbol not in result and symbol in self.DEFAULT_DATA:
                    default = self.DEFAULT_DATA[symbol]
                    result[symbol] = {
                        "current": default["current"],
                        "change": default["change"],
                        "history": default["history"][-history_days:],
                    }

        return MarketDataResponse.parse_obj(result or self.DEFAULT_DATA)
