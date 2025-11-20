# Database Design - OC5 ML Deployment v1.0.0

## Overview

This document describes the PostgreSQL database schema for storing API requests and predictions for the HR Attrition Prediction API.

**Purpose:**
- Store all API prediction requests (audit trail)
- Store prediction results for analytics
- Enable data retention policy (365 days)
- Support future analytics and monitoring features

**Technology Stack:**
- PostgreSQL 15+
- SQLAlchemy ORM (Python)
- Alembic for migrations

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────┐
│           api_requests              │
├─────────────────────────────────────┤
│ PK  id                 UUID         │
│     created_at         TIMESTAMP    │
│     endpoint           VARCHAR(100) │
│     request_data       JSONB        │
│     client_ip          VARCHAR(45)  │
│     user_agent         TEXT         │
│     http_status        INTEGER      │
│     response_time_ms   INTEGER      │
└─────────────────┬───────────────────┘
                  │
                  │ 1:N
                  │
                  ▼
┌─────────────────────────────────────┐
│          predictions                │
├─────────────────────────────────────┤
│ PK  id                 UUID         │
│ FK  request_id         UUID         │
│     created_at         TIMESTAMP    │
│     employee_id        VARCHAR(50)  │ (nullable - from input)
│     attrition_prob     FLOAT        │
│     risk_level         VARCHAR(10)  │
│     model_version      VARCHAR(50)  │
│     prediction_date    TIMESTAMP    │
│     features_snapshot  JSONB        │
└─────────────────────────────────────┘
```

**Relationship:**
- One `api_requests` record can have **multiple** `predictions` (batch predictions)
- Each `predictions` record belongs to **one** `api_requests` record

---

## Table Definitions

### Table: `api_requests`

**Purpose:** Store metadata about every API request for audit and monitoring.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique request identifier |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Request timestamp (UTC) |
| `endpoint` | VARCHAR(100) | NOT NULL | API endpoint called (e.g., "/api/v1/predict") |
| `request_data` | JSONB | NOT NULL | Raw request payload (EmployeeFeatures) |
| `client_ip` | VARCHAR(45) | NULL | Client IP address (IPv4/IPv6) |
| `user_agent` | TEXT | NULL | HTTP User-Agent header |
| `http_status` | INTEGER | NOT NULL | HTTP response status code |
| `response_time_ms` | INTEGER | NULL | Request processing time in milliseconds |

**Indexes:**
- `idx_api_requests_created_at` ON `created_at` (for retention cleanup)
- `idx_api_requests_endpoint` ON `endpoint` (for analytics)
- `idx_api_requests_http_status` ON `http_status` (for error tracking)

**Data Retention:**
- Records older than 365 days will be automatically deleted
- Implemented via scheduled job or database trigger

---

### Table: `predictions`

**Purpose:** Store prediction results for analytics and model monitoring.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique prediction identifier |
| `request_id` | UUID | FOREIGN KEY → api_requests(id), NOT NULL | Reference to API request |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Prediction timestamp (UTC) |
| `employee_id` | VARCHAR(50) | NULL | Employee ID from input (if provided) |
| `attrition_prob` | FLOAT | NOT NULL, CHECK (attrition_prob >= 0 AND attrition_prob <= 1) | Predicted attrition probability (0-1) |
| `risk_level` | VARCHAR(10) | NOT NULL, CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')) | Risk category |
| `model_version` | VARCHAR(50) | NOT NULL | Model version used (e.g., "xgb_enhanced_v1.0") |
| `prediction_date` | TIMESTAMP | NOT NULL | Timestamp from prediction response |
| `features_snapshot` | JSONB | NULL | Preprocessed features used for prediction |

**Indexes:**
- `idx_predictions_created_at` ON `created_at` (for retention cleanup)
- `idx_predictions_request_id` ON `request_id` (for joins)
- `idx_predictions_risk_level` ON `risk_level` (for analytics)
- `idx_predictions_model_version` ON `model_version` (for A/B testing)
- `idx_predictions_employee_id` ON `employee_id` (for employee history)

**Foreign Key:**
- `FOREIGN KEY (request_id) REFERENCES api_requests(id) ON DELETE CASCADE`
  - CASCADE: When an api_request is deleted, its predictions are also deleted

**Data Retention:**
- Records older than 365 days will be automatically deleted
- Cascade deletion via FK ensures consistency

---

## UML Class Diagram (SQLAlchemy Models)

```
┌──────────────────────────────────────────┐
│          APIRequest                       │
├──────────────────────────────────────────┤
│ + id: UUID                               │
│ + created_at: DateTime                   │
│ + endpoint: String(100)                  │
│ + request_data: JSON                     │
│ + client_ip: String(45)                  │
│ + user_agent: Text                       │
│ + http_status: Integer                   │
│ + response_time_ms: Integer              │
├──────────────────────────────────────────┤
│ + predictions: List[Prediction]          │  (relationship)
└────────────┬─────────────────────────────┘
             │
             │ 1
             │
             │
             │ *
┌────────────┴─────────────────────────────┐
│          Prediction                       │
├──────────────────────────────────────────┤
│ + id: UUID                               │
│ + request_id: UUID                       │  (FK)
│ + created_at: DateTime                   │
│ + employee_id: String(50)                │
│ + attrition_prob: Float                  │
│ + risk_level: String(10)                 │
│ + model_version: String(50)              │
│ + prediction_date: DateTime              │
│ + features_snapshot: JSON                │
├──────────────────────────────────────────┤
│ + request: APIRequest                    │  (relationship)
└──────────────────────────────────────────┘
```

---

## Data Types Rationale

### UUID vs SERIAL for Primary Keys
- **Choice:** UUID (universally unique identifier)
- **Rationale:**
  - Better for distributed systems
  - No sequential ID leaking (privacy/security)
  - Easy to merge data from multiple sources
  - Slightly larger storage (16 bytes vs 4/8 bytes)

### JSONB vs JSON
- **Choice:** JSONB (binary JSON)
- **Rationale:**
  - Faster queries and indexing
  - Supports GIN indexes for efficient searches
  - Slight overhead on insert (decompress/compress)
  - Better for analytics queries

### TIMESTAMP
- **Always store in UTC**
- Convert to local timezone in application layer
- Prevents timezone confusion

---

## Storage Estimates

### Assumptions
- Average API requests: 1,000 per day
- Average batch size: 1 prediction per request (conservative)
- 365-day retention

### Size Calculations

**api_requests table:**
- UUID (16 bytes) + TIMESTAMP (8 bytes) + VARCHAR(100) (100 bytes avg)
- JSONB (~500 bytes avg for EmployeeFeatures)
- VARCHAR(45) (15 bytes avg) + TEXT (50 bytes avg) + INTEGER (8 bytes)
- **Total per row:** ~700 bytes

**predictions table:**
- UUID (16 bytes) + UUID FK (16 bytes) + TIMESTAMP (8 bytes)
- VARCHAR(50) (20 bytes avg) + FLOAT (8 bytes) + VARCHAR(10) (6 bytes)
- VARCHAR(50) (20 bytes) + TIMESTAMP (8 bytes) + JSONB (200 bytes avg)
- **Total per row:** ~300 bytes

**Annual Storage:**
- api_requests: 1,000 requests/day × 365 days × 700 bytes = **255 MB**
- predictions: 1,000 predictions/day × 365 days × 300 bytes = **110 MB**
- **Total:** ~365 MB/year (excluding indexes)
- **With indexes:** ~500-600 MB/year

**Conclusion:** Very manageable storage footprint.

---

## Data Retention Strategy

### Requirement
- Keep data for 365 days
- Delete older records automatically

### Implementation Options

#### Option A: PostgreSQL Scheduled Job (pg_cron)
```sql
-- Run daily at 2 AM UTC
SELECT cron.schedule('cleanup-old-data', '0 2 * * *', $$
    DELETE FROM api_requests
    WHERE created_at < NOW() - INTERVAL '365 days';
$$);
```

**Pros:**
- Native PostgreSQL solution
- Efficient (runs in database)
- Automatic cascade to predictions

**Cons:**
- Requires pg_cron extension
- Not available on all PostgreSQL hosts

#### Option B: Application-Level Scheduled Job (Recommended)
```python
# Scheduled task (e.g., APScheduler, Celery)
async def cleanup_old_data():
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    await db.execute(
        delete(APIRequest).where(APIRequest.created_at < cutoff_date)
    )
```

**Pros:**
- No extension required
- Easy to test and monitor
- Can add logging/alerts
- Portable across databases

**Cons:**
- Requires application to be running
- Slight overhead

**Recommended:** Option B (application-level) for better control and portability.

---

## Security & Privacy Considerations

### Sensitive Data in request_data
**Issue:** `request_data` JSONB may contain PII (personally identifiable information).

**Mitigation Strategies:**
1. **Anonymization:**
   - Hash or remove `employee_id` before storage
   - Store only aggregated features, not raw data

2. **Encryption:**
   - Use PostgreSQL transparent data encryption (TDE)
   - Encrypt JSONB fields at application level

3. **Access Control:**
   - Restrict database user permissions
   - Use row-level security (RLS) if needed

4. **Compliance:**
   - GDPR: Implement right to erasure (delete by employee_id)
   - Document data retention policy
   - Add consent tracking if required

### Recommended Approach (for v1.0.0)
- Store data as-is for analytics (justified business need)
- Implement 365-day retention (data minimization)
- Add database-level access controls
- Document data handling in privacy policy
- Plan for future encryption (v1.1.0)

---

## Migration Plan (Alembic)

### Initial Migration (v1.0.0)

```python
# alembic/versions/001_initial_schema.py

def upgrade():
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create api_requests table
    op.create_table(
        'api_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('endpoint', sa.String(100), nullable=False),
        sa.Column('request_data', JSONB, nullable=False),
        sa.Column('client_ip', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('http_status', sa.Integer, nullable=False),
        sa.Column('response_time_ms', sa.Integer)
    )

    # Create indexes
    op.create_index('idx_api_requests_created_at', 'api_requests', ['created_at'])
    op.create_index('idx_api_requests_endpoint', 'api_requests', ['endpoint'])
    op.create_index('idx_api_requests_http_status', 'api_requests', ['http_status'])

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('request_id', UUID(as_uuid=True), sa.ForeignKey('api_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('employee_id', sa.String(50)),
        sa.Column('attrition_prob', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(10), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('features_snapshot', JSONB)
    )

    # Create indexes
    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'])
    op.create_index('idx_predictions_request_id', 'predictions', ['request_id'])
    op.create_index('idx_predictions_risk_level', 'predictions', ['risk_level'])
    op.create_index('idx_predictions_model_version', 'predictions', ['model_version'])
    op.create_index('idx_predictions_employee_id', 'predictions', ['employee_id'])

    # Add constraints
    op.create_check_constraint(
        'check_attrition_prob_range',
        'predictions',
        'attrition_prob >= 0 AND attrition_prob <= 1'
    )
    op.create_check_constraint(
        'check_risk_level_values',
        'predictions',
        "risk_level IN ('LOW', 'MEDIUM', 'HIGH')"
    )

def downgrade():
    op.drop_table('predictions')
    op.drop_table('api_requests')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
```

---

## Analytics Queries (Examples)

### 1. Daily Prediction Volume
```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_predictions,
    COUNT(DISTINCT request_id) as total_requests
FROM predictions
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 2. Risk Distribution
```sql
SELECT
    risk_level,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM predictions
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY risk_level;
```

### 3. Average Attrition Probability by Department
```sql
SELECT
    request_data->>'departement' as department,
    AVG(p.attrition_prob) as avg_attrition_prob,
    COUNT(*) as prediction_count
FROM predictions p
JOIN api_requests r ON p.request_id = r.id
WHERE p.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY request_data->>'departement'
ORDER BY avg_attrition_prob DESC;
```

### 4. API Response Time Metrics
```sql
SELECT
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_response_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_ms
FROM api_requests
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY endpoint;
```

### 5. Model Version Usage
```sql
SELECT
    model_version,
    COUNT(*) as prediction_count,
    MIN(created_at) as first_used,
    MAX(created_at) as last_used
FROM predictions
GROUP BY model_version
ORDER BY last_used DESC;
```

---

## Future Enhancements

### v1.1.0: Feedback Loop
- Add `actual_attrition` column to predictions (nullable)
- Update when employee actually leaves or stays
- Calculate model accuracy over time

```sql
ALTER TABLE predictions
ADD COLUMN actual_attrition BOOLEAN NULL,
ADD COLUMN feedback_date TIMESTAMP NULL;
```

### v1.2.0: User Authentication
- Add `users` table
- Add `api_keys` table
- Link `api_requests.user_id` to users
- Implement rate limiting per user

### v1.3.0: Model Explainability
- Add `shap_values` JSONB column to predictions
- Store SHAP feature importance for each prediction
- Enable API endpoint to fetch explanations

### v1.4.0: Batch Job Tracking
- Add `batch_jobs` table
- Track long-running batch predictions
- Support async processing

---

## Deployment Checklist

- [ ] PostgreSQL 15+ instance provisioned
- [ ] Database created: `oc5_ml_api_prod`
- [ ] User created with appropriate permissions
- [ ] Connection string configured in environment variables
- [ ] Alembic migrations initialized
- [ ] Initial migration run: `alembic upgrade head`
- [ ] Verify tables created: `\dt` in psql
- [ ] Verify indexes created: `\di` in psql
- [ ] Test insert/select on both tables
- [ ] Configure connection pooling (SQLAlchemy)
- [ ] Set up automated backups (daily)
- [ ] Configure retention cleanup job
- [ ] Set up monitoring alerts (disk space, query performance)
- [ ] Document connection details securely (password manager)

---

## Database Configuration

### SQLAlchemy Connection String
```python
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = "postgresql+asyncpg://oc5_user:secure_password@localhost:5432/oc5_ml_api_prod"
```

### Connection Pool Settings (Recommended)
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # Number of connections to maintain
    max_overflow=20,       # Additional connections if pool full
    pool_timeout=30,       # Timeout waiting for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False             # Set to True for SQL debugging
)
```

---

## Summary

**Database Design Highlights:**
- ✅ Two-table design: `api_requests` + `predictions`
- ✅ 1:N relationship (one request → many predictions)
- ✅ UUID primary keys for security and scalability
- ✅ JSONB for flexible storage and fast queries
- ✅ Comprehensive indexing for performance
- ✅ 365-day retention policy (application-level cleanup)
- ✅ Cascade deletion for data consistency
- ✅ ~500-600 MB/year storage footprint
- ✅ Ready for analytics and monitoring
- ✅ Migration strategy with Alembic

**Next Steps:**
1. Review and approve this design
2. Implement SQLAlchemy models
3. Create Alembic migration
4. Update API to log requests/predictions
5. Implement cleanup job
6. Test with sample data
7. Deploy to production

---

*Version: 1.0.0*
*Last Updated: 2025-11-19*
*Author: Database design for OC5 ML Deployment project*
