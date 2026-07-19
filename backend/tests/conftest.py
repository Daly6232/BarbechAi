import os
import sys
import uuid
from pathlib import Path

# Ensure "app" package is importable regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# CRITICAL: these must be set before any `app.*` module is imported, since
# app.core.config reads them once at import time via `settings = Settings()`.
# A fresh, disposable SQLite file per test run — never touches the real
# database, no matter what DATABASE_URL is set to in the actual environment.
TEST_DB_PATH = Path(__file__).resolve().parent / "_test_barbechai.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production-use"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402

from app.database import init_db, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Fresh schema once per test session. Tests use unique emails/names
    (see `unique_email` fixture) rather than per-test transaction rollback,
    since the app's SessionLocal usage pattern (commit-per-call inside each
    service function) isn't set up for nested-transaction test isolation."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    init_db()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def unique_email():
    return f"test-{uuid.uuid4().hex[:12]}@example.com"
