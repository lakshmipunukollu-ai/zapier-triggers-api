"""Test configuration — uses SQLite in-memory and mocked Redis."""
import json
import os
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine, event, String, TypeDecorator, Text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


# Patch JSONB before importing app modules
class JSONType(TypeDecorator):
    """SQLite-compatible JSON column type."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


# Monkey-patch JSONB in postgresql dialect to use our JSON type for SQLite
import sqlalchemy.dialects.postgresql as pg_dialect
_original_jsonb = pg_dialect.JSONB
pg_dialect.JSONB = JSONType

# Also patch in the module cache for already-imported modules
import app.models.event as event_module
# Re-patch the Event model's payload column type
# This is handled by the dialect adapter above

# Now import app modules
from app.database import Base, get_db
from app.redis_client import get_redis
from app.main import app

# Restore JSONB after import (in case other tests need it)
# pg_dialect.JSONB = _original_jsonb  # Don't restore, keep patched for table creation

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MockRedis:
    """In-memory Redis mock for testing."""

    def __init__(self):
        self._data = {}
        self._lists = {}

    def ping(self):
        return True

    def setex(self, key, time, value):
        self._data[key] = value

    def get(self, key):
        return self._data.get(key)

    def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
            self._lists.pop(key, None)

    def lpush(self, key, *values):
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].insert(0, v)

    def rpop(self, key):
        lst = self._lists.get(key, [])
        if lst:
            return lst.pop()
        return None

    def exists(self, key):
        return key in self._data or key in self._lists


mock_redis = MockRedis()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_redis():
    return mock_redis


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the test session."""
    from app.models.event import Event
    from app.models.subscription import Subscription
    from app.models.delivery_log import DeliveryLog

    # Drop old enum type references that SQLite doesn't support
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove(TEST_DB_PATH)
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
def clean_tables():
    """Clean tables between tests."""
    yield
    db = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()
    mock_redis._data.clear()
    mock_redis._lists.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for direct DB operations in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
