# Testing Patterns

**Analysis Date:** 2025-02-20

## Test Framework

**Backend:**
- Runner: pytest 8.3.4
- Async support: pytest-asyncio 0.24.0
- Client: FastAPI `TestClient` from `fastapi.testclient`
- Config: No `pytest.ini` or `pyproject.toml` with pytest config; uses defaults

**Frontend:**
- Runner: Not configured. `package.json` has no `"test"` script.
- Jest/Vitest: Not detected (no jest.config, vitest.config, or test dependencies)

**Run Commands:**
```bash
# Backend
cd backend
pytest                    # Run all tests
pytest tests/ -v          # Verbose

# Frontend (per README)
npm test                  # Script not present in package.json — not runnable
```

## Test File Organization

**Backend Location:**
- `backend/tests/` — pytest discovers `test_*.py` files
- `backend/test_auth.py` — standalone script at backend root (not pytest)
- `backend/test_supabase_connection.py` — standalone connection test at backend root
- `librework/test_all_features.py` — manual E2E script at project root

**Pattern:** Mixed. Official tests live in `backend/tests/`; ad-hoc scripts live at backend or project root.

**Naming:**
- Pytest: `test_main.py` (prefix `test_`)
- Standalone: `test_auth.py`, `test_supabase_connection.py`, `test_all_features.py`

**Frontend:** No test files (no `*.test.ts`, `*.spec.ts`, `__tests__/`)

## Test Structure

**Pytest suite (`backend/tests/test_main.py`):**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to LibreWork API"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# Note: Add more comprehensive tests for each endpoint
# These would require mocking Supabase or using a test database
```

**Patterns:**
- Synchronous `def test_*` (no async)
- `TestClient(app)` instantiated at module level
- Direct `assert response.status_code` and `assert response.json()`
- Docstrings describe what is tested

## Standalone / Manual Tests

**`backend/test_auth.py`:** Manual HTTP tests against running server
- Uses `requests` to hit `http://localhost:8000/api/v1`
- Tests registration, login, get current user
- Prints success/failure; exits on connection error
- Run: `python test_auth.py` (server must be running)

**`backend/test_supabase_connection.py`:** Database connectivity check
- Uses `supabase` client; loads `.env` via `dotenv`
- Queries `users` table with `limit(1)`
- Prints SUCCESS/ERROR; no assertions

**`librework/test_all_features.py`:** Full E2E feature script
- Uses `requests` against `http://127.0.0.1:8000`
- Tests: health, auth, availability, favorites, search, activity, loyalty, notifications, calendar, groups
- Requires backend running; uses global state (`auth_token`, `user_id`, etc.)
- Prints `[OK]` / `[FAIL]` / `[INFO]`; exits with 0/1 based on pass/fail

## Mocking

**Framework:** Not used in current tests.

**Current approach:** Tests hit real app via `TestClient`; `test_main.py` only covers root and health endpoints that do not call Supabase.

**Comment in `test_main.py`:**
> These would require mocking Supabase or using a test database

**Recommendation for new tests:** Mock `get_supabase()` or patch `app.core.supabase` to avoid hitting real DB. No existing fixtures or `conftest.py`.

## Fixtures and Factories

**Location:** No fixtures or factories detected. No `conftest.py`.

**Test Data:** Hardcoded in scripts (e.g. `test_auth.py`: `"test.user@gmail.com"`, `"test123456"`).

## Coverage

**Requirements:** None enforced. No `pytest-cov` or coverage config.

**View Coverage:** Not configured.

## Test Types

**Unit Tests:**
- Minimal: `test_main.py` exercises two endpoints in isolation
- No unit tests for services, schemas, or utilities

**Integration Tests:**
- Not present. Would need mocked Supabase or test DB.

**E2E Tests:**
- Manual scripts only: `test_all_features.py`, `test_auth.py`
- No Playwright, Cypress, or similar

## Common Patterns

**Async Testing:** Not used. All current pytest tests are sync.

**Error Testing:** Basic status checks only:
```python
assert response.status_code == 200
```

**Setup/Teardown:** None. No pytest fixtures.

## Where to Add New Tests

**Backend unit/integration:**
- Add `backend/tests/test_<module>.py` next to `test_main.py`
- Use `TestClient(app)`; mock `get_supabase` via `pytest` patch or `unittest.mock`
- Consider adding `backend/conftest.py` for shared fixtures and app override

**Backend auth tests:**
- `backend/tests/test_auth.py` — use TestClient + mocked Supabase
- Avoid modifying `backend/test_auth.py` (standalone script)

**Frontend:**
- No testing setup. Add Jest or Vitest, then create `frontend/src/**/__tests__/` or `*.test.tsx` next to components
- Configure `package.json` `"test"` script

## Gaps

- No `conftest.py` for shared fixtures
- No Supabase mocking in pytest
- No frontend tests
- No coverage reporting
- Manual E2E scripts depend on running backend

---

*Testing analysis: 2025-02-20*
