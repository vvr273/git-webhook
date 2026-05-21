import hashlib
import hmac
import json
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_engine
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def reset_db(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_github_webhooks.db")
    monkeypatch.setenv("STORE_RAW_PAYLOAD", "false")
    get_settings.cache_clear()
    get_engine.cache_clear()

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_signature() -> Callable[[str, dict], str]:
    def _make_signature(secret: str, payload: dict) -> str:
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    return _make_signature
