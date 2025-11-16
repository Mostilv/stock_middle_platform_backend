import logging
from typing import Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings
from app.utils.in_memory_db import InMemoryDatabase

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage the MongoDB connection used across the application."""

    def __init__(self) -> None:
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.mongodb_db: Optional[AsyncIOMotorDatabase] = None
        self._connected: bool = False
        self._default_db_name = settings.mongodb_db
        self._memory_databases: Dict[str, InMemoryDatabase] = {}

    async def connect_mongodb(self) -> bool:
        """Initialise the MongoDB client and verify availability."""
        if self._connected and self.mongodb_client:
            return True

        try:
            client = AsyncIOMotorClient(settings.mongodb_url)
            await client.admin.command("ping")
        except Exception as exc:
            if settings.debug:
                logger.warning(
                    "Failed to connect to MongoDB at %s (%s). Falling back to in-memory store.",
                    settings.mongodb_url,
                    exc,
                )
                self.mongodb_client = None
                if not isinstance(self.mongodb_db, InMemoryDatabase):
                    self.mongodb_db = InMemoryDatabase()
                self._memory_databases = {self._default_db_name: self.mongodb_db}
                self._connected = True
                logger.info("Using in-memory MongoDB mock database.")
                return True

            logger.exception("Failed to connect to MongoDB: %s", exc)
            self.mongodb_client = None
            self.mongodb_db = None
            self._connected = False
            return False

        self.mongodb_client = client
        self.mongodb_db = client[settings.mongodb_db]
        self._memory_databases = {}
        self._connected = True
        logger.info("Connected to MongoDB database '%s'", settings.mongodb_db)
        return True

    async def connect_all(self) -> bool:
        """Kept for backwards compatibility with the old API surface."""
        return await self.connect_mongodb()

    async def disconnect_mongodb(self) -> None:
        """Close the MongoDB connection if it exists."""
        if isinstance(self.mongodb_db, InMemoryDatabase):
            logger.info("Clearing in-memory MongoDB mock database")
            self.mongodb_db.reset()
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info("MongoDB connection closed")
        self.mongodb_client = None
        self.mongodb_db = None
        self._memory_databases = {}
        self._connected = False

    async def disconnect_all(self) -> None:
        """Mirror the historical API that closed every backend."""
        await self.disconnect_mongodb()

    async def health_check(self) -> Dict[str, bool]:
        """Return a simple health snapshot of the database layer."""
        status: Dict[str, bool] = {"mongodb": False}

        if isinstance(self.mongodb_db, InMemoryDatabase):
            status["mongodb"] = True
            return status

        if self.mongodb_client:
            try:
                await self.mongodb_client.admin.command("ping")
            except Exception as exc:
                logger.exception("MongoDB health check failed: %s", exc)
            else:
                status["mongodb"] = True

        return status

    def get_database(self, name: Optional[str] = None):
        if not name or name == self._default_db_name:
            if self.mongodb_db is None:
                raise RuntimeError("MongoDB is not connected.")
            return self.mongodb_db

        if isinstance(self.mongodb_db, InMemoryDatabase):
            if name not in self._memory_databases:
                self._memory_databases[name] = InMemoryDatabase()
            return self._memory_databases[name]

        if self.mongodb_client is None:
            raise RuntimeError("MongoDB is not connected.")
        return self.mongodb_client[name]

    def get_mongodb_collection(self, name: str):
        return self.get_database()[name]

    def get_collection(self, database: str, collection: str):
        return self.get_database(database)[collection]

    def is_connected(self) -> bool:
        return self._connected


db_manager = DatabaseManager()


class MongoDB:
    """Compatibility wrapper preserving the old import surface."""

    async def connect_to_mongo(self) -> bool:
        return await db_manager.connect_mongodb()

    async def close_mongo_connection(self) -> None:
        await db_manager.disconnect_mongodb()

    @property
    def client(self) -> AsyncIOMotorClient:
        if db_manager.mongodb_client is None:
            raise RuntimeError("MongoDB is not connected.")
        return db_manager.mongodb_client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if db_manager.mongodb_db is None:
            raise RuntimeError("MongoDB is not connected.")
        return db_manager.mongodb_db


mongodb = MongoDB()
