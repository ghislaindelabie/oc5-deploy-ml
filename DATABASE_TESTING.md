# Database Testing Strategy

This document explains how database integration tests work in this project.

## Overview

We use **conditional database tests** that only run when needed:

| Environment | Database Tests Run? | Why |
|-------------|-------------------|-----|
| Local dev | ❌ No | Fast feedback, no DB setup needed |
| Feature branch CI | ❌ No | Fast CI, don't need DB verification yet |
| **PR to main** | ✅ **Yes** | Critical verification before merge |
| Manual run | ✅ Yes (opt-in) | When you want to test DB locally |

## How It Works

### 1. Pytest Markers

Tests are marked with `@pytest.mark.database`:

```python
@pytest.mark.database  # This test requires database
async def test_prediction_logs_to_database():
    # Test implementation...
```

### 2. Default Behavior (Skip Database Tests)

By default, database tests are **skipped**:

```bash
# Normal test run (skips database tests)
pytest                  # ✅ 65 tests (API only)
pytest tests/           # ✅ 65 tests (API only)
```

This is configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "-m 'not database'"  # Skip database tests by default
```

### 3. Explicitly Run Database Tests

To run database tests locally:

```bash
# Run ONLY database tests
pytest -m database

# Run ALL tests (including database)
pytest -m ""  # Empty marker = run all
```

**Requirements:**
- `OC5_DATABASE_URL` must be set in environment
- Supabase database must be accessible

### 4. GitHub Actions Workflow

A separate workflow runs database tests **only on PRs to main**:

**`.github/workflows/database-tests.yml`**
```yaml
on:
  pull_request:
    branches: ["main"]  # Only on PR to main

jobs:
  database-tests:
    steps:
      - name: Run database integration tests
        env:
          OC5_DATABASE_URL: ${{ secrets.OC5_DATABASE_URL }}
        run: pytest -m database
```

## Test File Structure

```
tests/
├── test_api.py                    # ✅ Always run (API tests)
├── test_api_contracts.py          # ✅ Always run (Pydantic validation)
├── test_api_integration.py        # ✅ Always run (Integration tests)
├── test_model_service.py          # ✅ Always run (Model tests)
├── test_smoke.py                  # ✅ Always run (Smoke test)
└── test_database_integration.py   # ⏭️  Skipped by default (Database tests)
```

## Writing Database Tests

### Template

```python
import pytest
from sqlalchemy import select, func
from src.oc5_ml_deployment.database import DATABASE_ENABLED, APIRequest

# Mark as database test + skip if DB not configured
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(not DATABASE_ENABLED, reason="Needs DB"),
]

@pytest.mark.asyncio
async def test_something_with_database(db_session):
    """Test that requires database."""
    # Count records before
    result = await db_session.execute(select(func.count()).select_from(APIRequest))
    count_before = result.scalar()

    # Do something that writes to database
    # ...

    # Verify database was updated
    await db_session.rollback()  # Refresh session
    result = await db_session.execute(select(func.count()).select_from(APIRequest))
    count_after = result.scalar()

    assert count_after == count_before + 1
```

### Important Notes

1. **Always use `db_session` fixture** - It provides cleanup after each test
2. **Refresh session with `rollback()`** - TestClient doesn't commit automatically
3. **Clean up test data** - Use unique employee_ids like "TEST_DB_001"

## Setup Instructions

### Local Development

If you want to run database tests locally:

1. **Set environment variable:**
   ```bash
   export OC5_DATABASE_URL="postgresql+asyncpg://..."
   ```

2. **Run database tests:**
   ```bash
   pytest -m database
   ```

### GitHub Actions (CI/CD)

For PR to main, add these **GitHub Secrets** (not environment variables) to your repository:

**⚠️ IMPORTANT: These are SECRETS (not env vars) because they contain your database password!**

#### How to Add GitHub Secrets

1. Go to: **Settings → Secrets and variables → Actions → "New repository secret"**

2. Add two secrets:

   **Secret #1:**
   ```
   Name:  OC5_DATABASE_URL
   Value: postgresql+asyncpg://postgres.xxxx:PASSWORD@aws-0-xx.pooler.supabase.com:5432/postgres
   ```

   **Secret #2:**
   ```
   Name:  OC5_DIRECT_URL
   Value: postgresql+asyncpg://postgres.xxxx:PASSWORD@aws-0-xx.pooler.supabase.com:5432/postgres
   ```

#### GitHub Secrets Security

When stored as GitHub Secrets:
- ✅ Encrypted at rest in GitHub's vault
- ✅ Automatically redacted from logs (shows `***`)
- ✅ Not visible in UI after creation
- ✅ Only accessible via `${{ secrets.NAME }}` in workflows

The workflow will automatically run database tests on any PR to `main`.

## Current Database Tests

### `test_database_integration.py`

| Test | Description |
|------|-------------|
| `test_database_connection` | Verifies basic DB connectivity |
| `test_single_prediction_logs_to_database` | Checks single prediction logging |
| `test_batch_prediction_logs_to_database` | Checks batch prediction logging |
| `test_database_error_doesnt_break_prediction` | Validates graceful degradation |

## FAQ

**Q: Why not run database tests in every CI run?**
A: Database tests are slower, require secrets, and aren't needed for every feature branch. We only need to verify DB integration before merging to `main`.

**Q: What if I forget to run database tests?**
A: They run automatically on PR to `main` - you can't merge without them passing.

**Q: Can I run database tests locally without Supabase?**
A: No, these tests require a real PostgreSQL database. Use SQLite for unit tests if needed.

**Q: Do database tests clean up after themselves?**
A: Yes, the `db_session` fixture deletes test data created in the last 5 minutes after each test.

## Troubleshooting

### Error: "Database tests require OC5_DATABASE_URL"

**Solution:** Set the environment variable:
```bash
export OC5_DATABASE_URL="postgresql+asyncpg://..."
pytest -m database
```

### Error: "prepared statement already exists"

**Solution:** This is a pgbouncer issue. Use direct connection (port 5432) instead of pooled (port 6543).

### Tests pass locally but fail in GitHub Actions

**Solution:** Check that GitHub secrets are configured correctly:
- Go to Settings → Secrets and variables → Actions
- Verify `OC5_DATABASE_URL` and `OC5_DIRECT_URL` are set

## Summary

```bash
# 🏃‍♂️ Fast: Local development (no database)
pytest                     # 65 tests, ~2 seconds

# 🏃‍♂️ Fast: Feature branch CI (no database)
pytest                     # 65 tests, ~2 seconds

# 🐢 Slow: PR to main (with database)
pytest -m ""               # 69 tests, ~5 seconds

# 🎯 Targeted: Database only
pytest -m database         # 4 tests, ~3 seconds
```

This strategy gives us:
- ✅ Fast feedback for daily development
- ✅ Comprehensive testing before production
- ✅ No database setup burden for contributors
- ✅ Confidence that DB integration works
