#!/usr/bin/env python3
"""Initialize a default admin account in MongoDB."""

import asyncio
import os
import sys
from typing import Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import mongodb, db_manager
from app.services.user_service import UserService
from app.utils.in_memory_db import InMemoryDatabase


def get_admin_credentials() -> Tuple[str, str, str, str]:
    """Read admin credentials from environment variables with sensible defaults."""
    username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    full_name = os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator")
    return username, email, password, full_name


async def create_superuser() -> None:
    try:
        if not await mongodb.connect_to_mongo():
            print(
                "Failed to connect to MongoDB. Check your connection settings and try again."
            )
            return

        if isinstance(db_manager.mongodb_db, InMemoryDatabase):
            print(
                "MongoDB connection fell back to the in-memory store.\n"
                "Please start a MongoDB instance (or set DEBUG=False) and rerun this script."
            )
            return

        username, email, password, full_name = get_admin_credentials()
        user_service = UserService()

        existing_admin = await user_service.get_user_by_username(username)
        if existing_admin:
            print(f"Admin user '{username}' already exists. No action taken.")
            return

        admin_user = await user_service.create_superuser(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
        )

        print("Admin account created successfully.")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print("Remember to change the password after first login.")
    except Exception as exc:
        print(f"Failed to create admin user: {exc}")
    finally:
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_superuser())
