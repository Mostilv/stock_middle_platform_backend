import datetime

from app.models.settings import SettingsData
from app.services.collection_service import BaseCollectionService


class SettingsService(BaseCollectionService):
    DEFAULT_SETTINGS = SettingsData(
        emailConfigs=[
            {
                "id": "1",
                "email": "admin@example.com",
                "remark": "管理员邮箱",
                "enabled": True,
            },
            {
                "id": "2",
                "email": "trader@example.com",
                "remark": "交易员邮箱",
                "enabled": True,
            },
        ],
        notificationTemplates=[
            {
                "id": "1",
                "name": "通知模板",
                "subject": "投资组合调仓通知 - {{date}}",
                "content": (
                    "策略名称：{{strategyName}}\n"
                    "委托时间：{{orderTime}}\n"
                    "{{#orders}}{{stock}}|{{quantity}}|{{orderType}}|{{price}}|"
                    "{{action}}|{{position}}\n{{/orders}}"
                ),
                "enabled": True,
            }
        ],
    )

    def __init__(self) -> None:
        super().__init__("settings_data")

    async def get_settings(self, username: str) -> SettingsData:
        document = await self.collection.find_one({"username": username})
        if not document:
            await self.collection.update_one(
                {"username": username},
                {
                    "$setOnInsert": {
                        "username": username,
                        "data": self.DEFAULT_SETTINGS.dict(),
                        "updated_at": datetime.datetime.utcnow(),
                    }
                },
                upsert=True,
            )
            document = await self.collection.find_one({"username": username})
        payload = (document or {}).get("data") or self.DEFAULT_SETTINGS.dict()
        return SettingsData.parse_obj(payload)

    async def save_settings(self, username: str, data: SettingsData) -> None:
        await self.collection.update_one(
            {"username": username},
            {
                "$set": {
                    "data": data.dict(),
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )
