from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    os.environ["ENV"] = "test"
    os.environ["API_KEY"] = "test-key"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["MYSQL_HOST"] = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    os.environ["MONGO_URI"] = "memory://"
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
