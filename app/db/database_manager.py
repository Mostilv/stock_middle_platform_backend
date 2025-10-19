"""
Application level helpers for managing database connections.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from .database import db_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler that opens and closes the MongoDB connection."""
    logger.info("Starting database layer initialisation")
    try:
        connected = await db_manager.connect_all()
        if connected:
            logger.info("MongoDB connection established")
        else:
            logger.warning("MongoDB connection could not be established during startup")
    except Exception:
        logger.exception("Unexpected error while connecting to MongoDB")

    app.state.db_manager = db_manager

    try:
        yield
    finally:
        logger.info("Shutting down database layer")
        try:
            await db_manager.disconnect_all()
        except Exception:
            logger.exception("Unexpected error while closing MongoDB connections")


class DatabaseConnectionManager:
    """Small facade used by health checks and background tasks."""

    def __init__(self) -> None:
        self.connected: bool = False
        self.health_status: Dict[str, bool] = {}

    async def initialize(self) -> bool:
        logger.info("Initialising database connection")
        self.connected = await db_manager.connect_all()
        self.health_status = await db_manager.health_check()
        return self.connected

    async def shutdown(self) -> None:
        logger.info("Closing database connection")
        await db_manager.disconnect_all()
        self.connected = False
        self.health_status = {}

    async def health_check(self) -> Dict[str, bool]:
        self.health_status = await db_manager.health_check()
        return self.health_status

    def is_connected(self) -> bool:
        return self.connected or db_manager.is_connected()

    def get_health_status(self) -> Dict[str, bool]:
        return self.health_status


db_connection_manager = DatabaseConnectionManager()
