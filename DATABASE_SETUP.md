# Database Setup Guide - OC5 ML Deployment v1.0.0

Quick guide to set up and test the PostgreSQL database integration.

## Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase account created)
- Dependencies installed

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependencies for v1.0.0:**
- `asyncpg==0.29.0` - Async PostgreSQL driver
- `alembic==1.13.2` - Database migrations
- `greenlet==3.0.3` - Required by SQLAlchemy async

## Step 2: Configure Environment Variables

Create `.env` file in project root (already done for you):

```bash
# .env
OC5_DATABASE_URL=postgresql+asyncpg://postgres.xxx:[PASSWORD]@aws-1-eu-west-3.pooler.supabase.com:6543/postgres?pgbouncer=true
OC5_DIRECT_URL=postgresql+asyncpg://postgres.xxx:[PASSWORD]@aws-1-eu-west-3.pooler.supabase.com:5432/postgres
```

**Note:** Two URLs are needed:
- `OC5_DATABASE_URL` - For app (with pgbouncer pooling)
- `OC5_DIRECT_URL` - For Alembic migrations (direct connection)

## Step 3: Run Database Migrations

```bash
# Create alembic.ini from template (first time only)
cp alembic.ini.template alembic.ini

# Run migrations to create tables
alembic upgrade head
```

**What this does:**
- Connects to Supabase PostgreSQL
- Creates `api_requests` table
- Creates `predictions` table
- Creates indexes for performance

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial schema for API requests and predictions logging
```

## Step 4: Verify Tables Created

**Option A: Using psql (if installed)**
```bash
psql "postgresql://postgres.xjdgwkhueyhonyhbfwpw:[PASSWORD]@aws-1-eu-west-3.pooler.supabase.com:5432/postgres" -c "\dt"
```

**Option B: Using Supabase Dashboard**
1. Go to https://supabase.com
2. Select your project
3. Go to "Table Editor"
4. You should see: `api_requests`, `predictions`, `alembic_version`

## Step 5: Test the API

```bash
# Start the API
uvicorn src.oc5_ml_deployment.api.main:app --reload

# Or use the demo script
python demo_api_locally.py
```

**Check startup logs:**
```
INFO:     Starting up API...
INFO:     Model loaded successfully
INFO:     Database logging is ENABLED  ← Should say ENABLED
INFO:     Application startup complete.
```

## Step 6: Make a Test Prediction

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "genre": "Male",
    "statut_marital": "Married",
    "departement": "Sales",
    "poste": "Sales Executive",
    "domaine_etude": "Life Sciences",
    "revenu_mensuel": 5000,
    "nombre_experiences_precedentes": 3,
    "nombre_heures_travailless": 40,
    "annees_dans_le_poste_actuel": 2,
    "satisfaction_employee_environnement": 4,
    "note_evaluation_precedente": 3,
    "satisfaction_employee_nature_travail": 4,
    "satisfaction_employee_equipe": 3,
    "satisfaction_employee_equilibre_pro_perso": 3,
    "note_evaluation_actuelle": 3,
    "nombre_participation_pee": 1,
    "nb_formations_suivies": 2,
    "nombre_employee_sous_responsabilite": 0,
    "distance_domicile_travail": 10,
    "niveau_education": 3,
    "annees_depuis_la_derniere_promotion": 1,
    "annes_sous_responsable_actuel": 2,
    "heure_supplementaires": "No"
  }'
```

**Expected response:**
```json
{
  "prediction": {
    "will_leave": false,
    "probability_leave": 0.23,
    "probability_stay": 0.77,
    "risk_level": "LOW"
  },
  "metadata": {
    "model_version": "xgb_enhanced_v1.0",
    "prediction_time_ms": 42,
    "timestamp": "2025-11-19T18:00:00.000000Z"
  }
}
```

## Step 7: Verify Data Logged to Database

**Check in Supabase Dashboard:**

1. Go to Table Editor → `api_requests`
   - Should see 1 row with endpoint `/api/v1/predict`

2. Go to Table Editor → `predictions`
   - Should see 1 row with the prediction result

**Or use SQL:**
```sql
SELECT COUNT(*) FROM api_requests;
SELECT COUNT(*) FROM predictions;
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 5;
```

## Troubleshooting

### Error: "relation 'api_requests' does not exist"
**Solution:** Run migrations
```bash
alembic upgrade head
```

### Error: "Database logging is DISABLED"
**Solution:** Check environment variable is set
```bash
echo $OC5_DATABASE_URL
# If empty, source .env file or export manually
export OC5_DATABASE_URL="postgresql+asyncpg://..."
```

### Error: "asyncpg.exceptions.InvalidPasswordError"
**Solution:** Check password in .env file matches Supabase

### Error: "Could not connect to server"
**Solution:** Check Supabase project is running (not paused)

## Testing Without Database

The API works without database! Just don't set `OC5_DATABASE_URL`:

```bash
unset OC5_DATABASE_URL
uvicorn src.oc5_ml_deployment.api.main:app --reload
```

**Startup logs will show:**
```
INFO:     Database logging is DISABLED - predictions will not be saved
```

Predictions still work, they just aren't logged to database.

## Data Retention

The database implements a 365-day retention policy.

**Manual cleanup (if needed):**
```python
from src.oc5_ml_deployment.database import crud, AsyncSessionLocal

async def cleanup():
    async with AsyncSessionLocal() as session:
        deleted = await crud.cleanup_old_data(session, retention_days=365)
        print(f"Deleted {deleted} old requests")

import asyncio
asyncio.run(cleanup())
```

**Automated cleanup:** Plan to add scheduled job in v1.1.0

## GitHub Secrets (for CI/CD)

Add these secrets to GitHub repository:

1. Go to Settings → Secrets and variables → Actions
2. Add:
   - `OC5_DATABASE_URL` = (your Supabase pooled URL)
   - `OC5_DIRECT_URL` = (your Supabase direct URL)

## HF Spaces Deployment

Add environment variables in HF Spaces:

1. Go to Settings → Variables
2. Add:
   - `OC5_DATABASE_URL` = (your Supabase pooled URL)

**Note:** Don't need `OC5_DIRECT_URL` on HF Spaces (migrations run locally)

## Summary

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env (already done)
# (contains OC5_DATABASE_URL and OC5_DIRECT_URL)

# 3. Run migrations
alembic upgrade head

# 4. Start API
uvicorn src.oc5_ml_deployment.api.main:app --reload

# 5. Test prediction
curl -X POST http://localhost:8000/api/v1/predict -H "Content-Type: application/json" -d @test_payload.json

# 6. Verify in Supabase dashboard
# Tables: api_requests, predictions
```

---

**Ready to test!** Follow steps 1-6 above.
