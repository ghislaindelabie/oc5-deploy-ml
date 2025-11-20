# TODO for v1.1.0

## Priority Tasks

### 1. Fix Database Integration Tests
**Issue:** Event loop conflict between TestClient (sync) and async database operations

**Current Status:**
- ✅ Database logging works perfectly (manually verified with 4 predictions logged to Supabase)
- ❌ 2 of 4 database tests fail due to async event loop issues
- ✅ Tests pass: test_database_connection, test_database_error_doesnt_break_prediction
- ❌ Tests fail: test_single_prediction_logs_to_database, test_batch_prediction_logs_to_database

**Error:**
```
RuntimeError: Task got Future attached to a different loop
```

**Solution:**
Replace `fastapi.testclient.TestClient` with `httpx.AsyncClient` for database tests.

**Example:**
```python
# Instead of:
from fastapi.testclient import TestClient
client = TestClient(app)

# Use:
import httpx
async with httpx.AsyncClient(app=app, base_url="http://test") as client:
    response = await client.post("/api/v1/predict", json=data)
```

**Files to update:**
- `tests/test_database_integration.py` - Rewrite using httpx.AsyncClient
- `tests/conftest.py` - Add async_client fixture
- `.github/workflows/database-tests.yml.disabled` - Re-enable workflow

**References:**
- https://www.python-httpx.org/async/
- https://fastapi.tiangolo.com/advanced/async-tests/

---

### 2. Simplify Database Configuration

**Issue:** Two identical database URLs (OC5_DATABASE_URL and OC5_DIRECT_URL)

**Current Status:**
- Both use direct connection (port 5432)
- Originally designed for: pooled (6543) vs direct (5432)
- After pgbouncer issues: both simplified to direct connection
- Result: Redundant configuration

**Solution:**
Use single `OC5_DATABASE_URL` for both application and migrations.

**Changes needed:**
1. Update `alembic/env.py` to use `OC5_DATABASE_URL` (not `OC5_DIRECT_URL`)
2. Remove `OC5_DIRECT_URL` from:
   - GitHub Secrets
   - HF Spaces variables
   - Documentation (DATABASE_SETUP.md, DATABASE_TESTING.md)
   - .env.example

**Trade-off:** If we solve pgbouncer issues later and want pooling, we'd need to add it back (unlikely, easy to do).

---

### 3. Optional: Re-enable pgbouncer Connection Pooling

**Context:** Currently using direct connection to avoid prepared statement conflicts

**If needed:**
- Research asyncpg + pgbouncer + prepared statements
- Test with `prepared_statement_cache_size=0` or `statement_cache_size=0`
- Update OC5_DATABASE_URL to use port 6543
- Verify no "prepared statement already exists" errors

**Benefit:** Better performance at high concurrency (not critical for current traffic)

---

## Nice to Have

### 4. Add pytest-asyncio to pyproject.toml dev dependencies
Currently only in requirements.txt

### 5. Add Database Cleanup Scheduled Job
Implement automated 365-day data retention cleanup

### 6. Database Performance Monitoring
- Add metrics for query performance
- Monitor connection pool usage
- Alert on slow queries

---

## Version Notes

**v1.0.0 Status:**
- ✅ Database integration fully functional
- ✅ All 65 API tests passing
- ✅ Manually verified database logging works
- ⚠️ Database integration tests disabled (infrastructure issue, not code issue)

**v1.1.0 Goal:**
- ✅ Fix database tests with httpx.AsyncClient
- ✅ Simplify to single database URL
- ✅ 100% test coverage including database integration
