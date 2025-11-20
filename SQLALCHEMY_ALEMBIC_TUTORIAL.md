# SQLAlchemy & Alembic Tutorial

## Table of Contents
1. [Introduction](#introduction)
2. [SQLAlchemy Fundamentals](#sqlalchemy-fundamentals)
3. [Alembic Migrations](#alembic-migrations)
4. [Implementation for OC5 Project](#implementation-for-oc5-project)
5. [Best Practices](#best-practices)

---

## Introduction

### The Problem We're Solving

Imagine you're building an application that needs to store data. You have a few options:

**Option 1: Write Raw SQL**
```python
import psycopg2

conn = psycopg2.connect("postgresql://localhost/mydb")
cursor = conn.cursor()
cursor.execute("INSERT INTO predictions (id, attrition_prob) VALUES (%s, %s)", (123, 0.75))
conn.commit()
```

**Problems:**
- 😞 Writing SQL strings is error-prone (typos, syntax errors)
- 😞 No type checking (Python doesn't know what columns exist)
- 😞 Database-specific SQL (PostgreSQL ≠ MySQL ≠ SQLite)
- 😞 Difficult to test
- 😞 No automatic schema versioning

**Option 2: Use SQLAlchemy (ORM)**
```python
from sqlalchemy.orm import Session

prediction = Prediction(id=123, attrition_prob=0.75)
session.add(prediction)
session.commit()
```

**Benefits:**
- ✅ Pythonic code (objects, not strings)
- ✅ Type checking and autocomplete
- ✅ Database-agnostic (works with PostgreSQL, MySQL, SQLite, etc.)
- ✅ Easy to test (can mock objects)
- ✅ Combined with Alembic for schema versioning

---

## SQLAlchemy Fundamentals

### What is SQLAlchemy?

**SQLAlchemy** is a Python library that lets you interact with databases using Python objects instead of writing raw SQL.

**Two Main Components:**

1. **Core:** Low-level SQL builder (closer to raw SQL)
2. **ORM (Object-Relational Mapping):** High-level object interface (we'll focus on this)

### The ORM Pattern

**ORM = Object-Relational Mapping**

Maps Python classes (objects) to database tables (relations).

```
Python World                    Database World
─────────────                   ──────────────
Class Prediction        ←→      Table predictions
Instance prediction     ←→      Row in predictions
Attribute .attrition_prob ←→    Column attrition_prob
```

### Example: From Database to Python

**Database Table:**
```
predictions
┌──────────┬─────────────────┬────────────┐
│ id       │ attrition_prob  │ risk_level │
├──────────┼─────────────────┼────────────┤
│ uuid-123 │ 0.75            │ HIGH       │
│ uuid-456 │ 0.25            │ LOW        │
└──────────┴─────────────────┴────────────┘
```

**SQLAlchemy Model (Python Class):**
```python
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import DeclarativeBase
from uuid import UUID

class Base(DeclarativeBase):
    pass

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(UUID(as_uuid=True), primary_key=True)
    attrition_prob = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)
```

**Usage:**
```python
# Query all predictions
predictions = session.query(Prediction).all()

# Access like Python objects
for pred in predictions:
    print(f"ID: {pred.id}, Probability: {pred.attrition_prob}, Risk: {pred.risk_level}")
```

---

## Core SQLAlchemy Concepts

### 1. Declarative Base

**What:** The foundation for all your models.

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**Purpose:**
- All your models inherit from `Base`
- Tracks metadata about all tables
- Used by Alembic to detect schema changes

### 2. Models (Tables)

**What:** Python classes that represent database tables.

```python
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class Prediction(Base):
    __tablename__ = 'predictions'  # Name of the table in database

    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attrition_prob = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Key Elements:**

- `__tablename__`: Name of the table in the database
- `Column(...)`: Defines a column with type and constraints
- `primary_key=True`: Marks the primary key
- `nullable=False`: Column cannot be NULL (required)
- `default=...`: Default value for new records

### 3. Relationships (Foreign Keys)

**What:** Link between tables (like our api_requests → predictions relationship).

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class APIRequest(Base):
    __tablename__ = 'api_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String(100), nullable=False)

    # Relationship: One request has many predictions
    predictions = relationship("Prediction", back_populates="request", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey('api_requests.id'), nullable=False)
    attrition_prob = Column(Float, nullable=False)

    # Relationship: Each prediction belongs to one request
    request = relationship("APIRequest", back_populates="predictions")
```

**Usage:**
```python
# Create request with predictions
request = APIRequest(endpoint="/api/v1/predict/batch")
prediction1 = Prediction(attrition_prob=0.75, risk_level="HIGH")
prediction2 = Prediction(attrition_prob=0.25, risk_level="LOW")

request.predictions.append(prediction1)
request.predictions.append(prediction2)

session.add(request)
session.commit()

# Later, access predictions from request
request = session.query(APIRequest).first()
for pred in request.predictions:
    print(f"Probability: {pred.attrition_prob}")
```

**Relationship Parameters:**

- `back_populates`: Creates bidirectional relationship
- `cascade="all, delete-orphan"`: When request is deleted, delete its predictions too
- `lazy="select"`: How/when to load related objects (options: "select", "joined", "subquery")

### 4. Engine (Connection to Database)

**What:** The connection between SQLAlchemy and your database.

```python
from sqlalchemy import create_engine

# Synchronous engine
engine = create_engine(
    "postgresql://user:password@localhost:5432/oc5_ml_api",
    echo=True  # Print all SQL queries (useful for debugging)
)

# Async engine (for FastAPI with async/await)
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/oc5_ml_api",
    echo=True,
    pool_size=10,          # Max number of connections to keep open
    max_overflow=20        # Extra connections when pool is full
)
```

**Connection String Format:**
```
dialect+driver://username:password@host:port/database

Examples:
- PostgreSQL (sync):  postgresql://user:pass@localhost:5432/dbname
- PostgreSQL (async): postgresql+asyncpg://user:pass@localhost:5432/dbname
- SQLite:             sqlite:///path/to/file.db
- MySQL:              mysql+pymysql://user:pass@localhost:3306/dbname
```

### 5. Session (Database Transactions)

**What:** A workspace for database operations. Think of it like a shopping cart.

```python
from sqlalchemy.orm import Session

# Create session
session = Session(engine)

# Add items (not committed to DB yet)
prediction = Prediction(attrition_prob=0.75, risk_level="HIGH")
session.add(prediction)

# Commit (save to database)
session.commit()

# Rollback (cancel changes if error occurs)
try:
    session.add(bad_data)
    session.commit()
except:
    session.rollback()  # Undo changes
finally:
    session.close()  # Always close session
```

**Async Session (for FastAPI):**
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def add_prediction():
    async with AsyncSession(async_engine) as session:
        prediction = Prediction(attrition_prob=0.75, risk_level="HIGH")
        session.add(prediction)
        await session.commit()
        # Auto-closes when exiting 'with' block
```

### 6. Queries

**Reading Data from Database:**

```python
# Get all predictions
predictions = session.query(Prediction).all()

# Get first prediction
first_pred = session.query(Prediction).first()

# Filter by condition
high_risk = session.query(Prediction).filter(Prediction.risk_level == "HIGH").all()

# Filter with multiple conditions
recent_high_risk = session.query(Prediction).filter(
    Prediction.risk_level == "HIGH",
    Prediction.created_at > datetime(2025, 1, 1)
).all()

# Order by
sorted_preds = session.query(Prediction).order_by(Prediction.attrition_prob.desc()).all()

# Limit results
top_10 = session.query(Prediction).limit(10).all()

# Count
count = session.query(Prediction).filter(Prediction.risk_level == "HIGH").count()

# Join tables
results = session.query(Prediction, APIRequest).join(
    APIRequest, Prediction.request_id == APIRequest.id
).all()

# Async version
async with AsyncSession(async_engine) as session:
    result = await session.execute(
        select(Prediction).filter(Prediction.risk_level == "HIGH")
    )
    predictions = result.scalars().all()
```

---

## Alembic Migrations

### What is Alembic?

**Alembic** is a database migration tool for SQLAlchemy. It tracks and applies changes to your database schema over time.

**Analogy:** Alembic is like **Git for your database schema**.

- Git tracks changes to your code
- Alembic tracks changes to your database structure

### Why Do We Need Migrations?

**Scenario:** Your application evolves over time.

**Week 1:** You create the `predictions` table
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    attrition_prob FLOAT
);
```

**Week 2:** You realize you need a `risk_level` column
```sql
ALTER TABLE predictions ADD COLUMN risk_level VARCHAR(10);
```

**Week 3:** You need an index for performance
```sql
CREATE INDEX idx_risk_level ON predictions(risk_level);
```

**Problems Without Migrations:**

1. ❌ **Lost History:** How do you remember all the changes?
2. ❌ **Multiple Environments:** How do you sync dev, staging, production?
3. ❌ **Team Collaboration:** How do teammates get the same schema?
4. ❌ **Rollback:** How do you undo a change?
5. ❌ **Manual Work:** Running SQL scripts is error-prone

**With Alembic Migrations:**

1. ✅ **Version Control:** Each change is a versioned migration file
2. ✅ **Automatic Detection:** Alembic detects schema changes
3. ✅ **One Command:** `alembic upgrade head` applies all migrations
4. ✅ **Rollback:** `alembic downgrade -1` undoes the last migration
5. ✅ **Audit Trail:** See exactly what changed and when

### How Alembic Works

**Core Concept:** Alembic creates a special table called `alembic_version` in your database.

```
alembic_version
┌──────────────────┐
│ version_num      │
├──────────────────┤
│ abc123def456     │  ← Current migration version
└──────────────────┘
```

**Migration Files:** Python scripts that describe schema changes.

```
alembic/versions/
├── 001_abc123_initial_schema.py       ← First migration
├── 002_def456_add_risk_level.py       ← Second migration
└── 003_ghi789_add_indexes.py          ← Third migration
```

Each file has:
- **`upgrade()`**: How to apply the change (CREATE TABLE, ADD COLUMN, etc.)
- **`downgrade()`**: How to undo the change (DROP TABLE, DROP COLUMN, etc.)

### Alembic Setup

**1. Install Alembic:**
```bash
pip install alembic
```

**2. Initialize Alembic:**
```bash
alembic init alembic
```

This creates:
```
project/
├── alembic/
│   ├── versions/           ← Migration files go here
│   ├── env.py              ← Configuration for migrations
│   └── script.py.mako      ← Template for new migrations
├── alembic.ini             ← Alembic configuration file
└── src/
    └── models.py           ← Your SQLAlchemy models
```

**3. Configure Alembic (`alembic.ini`):**
```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:password@localhost:5432/oc5_ml_api
```

**4. Configure `env.py` (Important!):**
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from your_app.models import Base  # Import your Base

# Add your models' metadata
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### Creating Migrations

**Two Ways to Create Migrations:**

#### Method 1: Auto-Generate (Recommended)

Alembic compares your SQLAlchemy models to the database and generates migrations automatically.

```bash
# Create a new migration
alembic revision --autogenerate -m "add risk_level column"
```

Alembic generates:
```python
# alembic/versions/002_add_risk_level.py
"""add risk_level column

Revision ID: def456
Revises: abc123
Create Date: 2025-11-19 10:30:00
"""

def upgrade():
    op.add_column('predictions', sa.Column('risk_level', sa.String(10), nullable=True))

def downgrade():
    op.drop_column('predictions', 'risk_level')
```

#### Method 2: Manual Creation

For complex changes, create an empty migration and write it yourself.

```bash
alembic revision -m "custom migration"
```

Then edit the generated file:
```python
def upgrade():
    # Your custom SQL or operations
    op.execute("CREATE INDEX CONCURRENTLY idx_custom ON predictions(attrition_prob)")

def downgrade():
    op.execute("DROP INDEX idx_custom")
```

### Applying Migrations

**Upgrade to Latest:**
```bash
alembic upgrade head
```

**Upgrade to Specific Revision:**
```bash
alembic upgrade abc123
```

**Downgrade (Undo Last Migration):**
```bash
alembic downgrade -1
```

**Downgrade to Specific Revision:**
```bash
alembic downgrade abc123
```

**View Current Version:**
```bash
alembic current
```

**View Migration History:**
```bash
alembic history
```

### Migration Operations

Alembic provides many operations via the `op` object:

```python
from alembic import op
import sqlalchemy as sa

# Create table
op.create_table(
    'predictions',
    sa.Column('id', sa.UUID(), primary_key=True),
    sa.Column('attrition_prob', sa.Float(), nullable=False)
)

# Drop table
op.drop_table('predictions')

# Add column
op.add_column('predictions', sa.Column('risk_level', sa.String(10)))

# Drop column
op.drop_column('predictions', 'risk_level')

# Alter column
op.alter_column('predictions', 'risk_level', type_=sa.String(20))

# Create index
op.create_index('idx_risk_level', 'predictions', ['risk_level'])

# Drop index
op.drop_index('idx_risk_level')

# Create foreign key
op.create_foreign_key(
    'fk_prediction_request',
    'predictions', 'api_requests',
    ['request_id'], ['id'],
    ondelete='CASCADE'
)

# Execute raw SQL
op.execute("CREATE EXTENSION IF NOT EXISTS 'uuid-ossp'")
```

---

## Implementation for OC5 Project

Let me show you the complete implementation for your project.

### Step 1: Project Structure

```
oc5-ml-deployment/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── src/
│   └── oc5_ml_deployment/
│       ├── database/
│       │   ├── __init__.py
│       │   ├── models.py        ← SQLAlchemy models
│       │   ├── database.py      ← Database connection
│       │   └── crud.py          ← CRUD operations
│       └── api/
│           └── main.py          ← FastAPI app
└── requirements.txt
```

### Step 2: Database Connection (`database.py`)

```python
# src/oc5_ml_deployment/database/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/oc5_ml_api"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL (set to False in production)
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI
async def get_db():
    """Provide database session to FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Step 3: SQLAlchemy Models (`models.py`)

```python
# src/oc5_ml_deployment/database/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base

class APIRequest(Base):
    """Store metadata about API requests."""

    __tablename__ = 'api_requests'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Request metadata
    endpoint = Column(String(100), nullable=False, index=True)
    request_data = Column(JSONB, nullable=False)
    client_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)

    # Response metadata
    http_status = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)

    # Relationships
    predictions = relationship(
        "Prediction",
        back_populates="request",
        cascade="all, delete-orphan",  # Delete predictions when request is deleted
        lazy="selectin"  # Load predictions when loading request
    )

    def __repr__(self):
        return f"<APIRequest(id={self.id}, endpoint={self.endpoint}, created_at={self.created_at})>"


class Prediction(Base):
    """Store prediction results."""

    __tablename__ = 'predictions'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to API request
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_requests.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    prediction_date = Column(DateTime(timezone=True), nullable=False)

    # Employee data
    employee_id = Column(String(50), nullable=True, index=True)

    # Prediction results
    attrition_prob = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, index=True)

    # Features used for prediction
    features_snapshot = Column(JSONB, nullable=True)

    # Relationships
    request = relationship("APIRequest", back_populates="predictions")

    # Constraints
    __table_args__ = (
        CheckConstraint('attrition_prob >= 0 AND attrition_prob <= 1', name='check_attrition_prob_range'),
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name='check_risk_level_values'),
    )

    def __repr__(self):
        return f"<Prediction(id={self.id}, risk_level={self.risk_level}, attrition_prob={self.attrition_prob})>"
```

### Step 4: CRUD Operations (`crud.py`)

```python
# src/oc5_ml_deployment/database/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from .models import APIRequest, Prediction

# ============================================================================
# CREATE Operations
# ============================================================================

async def create_api_request(
    session: AsyncSession,
    endpoint: str,
    request_data: dict,
    client_ip: str,
    user_agent: str,
    http_status: int,
    response_time_ms: int
) -> APIRequest:
    """Create a new API request record."""
    request = APIRequest(
        endpoint=endpoint,
        request_data=request_data,
        client_ip=client_ip,
        user_agent=user_agent,
        http_status=http_status,
        response_time_ms=response_time_ms
    )
    session.add(request)
    await session.flush()  # Get the ID without committing
    return request


async def create_prediction(
    session: AsyncSession,
    request_id: uuid.UUID,
    employee_id: Optional[str],
    attrition_prob: float,
    risk_level: str,
    model_version: str,
    features_snapshot: Optional[dict] = None
) -> Prediction:
    """Create a new prediction record."""
    prediction = Prediction(
        request_id=request_id,
        employee_id=employee_id,
        attrition_prob=attrition_prob,
        risk_level=risk_level,
        model_version=model_version,
        prediction_date=datetime.utcnow(),
        features_snapshot=features_snapshot
    )
    session.add(prediction)
    await session.flush()
    return prediction


# ============================================================================
# READ Operations
# ============================================================================

async def get_request_by_id(session: AsyncSession, request_id: uuid.UUID) -> Optional[APIRequest]:
    """Get an API request by ID."""
    result = await session.execute(
        select(APIRequest).filter(APIRequest.id == request_id)
    )
    return result.scalar_one_or_none()


async def get_predictions_by_request(session: AsyncSession, request_id: uuid.UUID) -> List[Prediction]:
    """Get all predictions for a specific request."""
    result = await session.execute(
        select(Prediction).filter(Prediction.request_id == request_id)
    )
    return result.scalars().all()


async def get_recent_predictions(session: AsyncSession, limit: int = 100) -> List[Prediction]:
    """Get the most recent predictions."""
    result = await session.execute(
        select(Prediction)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_high_risk_predictions(session: AsyncSession, days: int = 30) -> List[Prediction]:
    """Get high-risk predictions from the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(Prediction)
        .filter(Prediction.risk_level == "HIGH", Prediction.created_at >= cutoff)
        .order_by(Prediction.created_at.desc())
    )
    return result.scalars().all()


# ============================================================================
# ANALYTICS Operations
# ============================================================================

async def get_prediction_count_by_risk(session: AsyncSession) -> dict:
    """Get count of predictions by risk level."""
    result = await session.execute(
        select(Prediction.risk_level, func.count(Prediction.id))
        .group_by(Prediction.risk_level)
    )
    return {risk: count for risk, count in result.all()}


async def get_average_attrition_prob(session: AsyncSession) -> float:
    """Get average attrition probability across all predictions."""
    result = await session.execute(
        select(func.avg(Prediction.attrition_prob))
    )
    return result.scalar() or 0.0


# ============================================================================
# DELETE Operations (Data Retention)
# ============================================================================

async def cleanup_old_data(session: AsyncSession, retention_days: int = 365) -> int:
    """Delete API requests and predictions older than retention period."""
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    # Delete old requests (predictions will cascade)
    result = await session.execute(
        delete(APIRequest).filter(APIRequest.created_at < cutoff_date)
    )

    deleted_count = result.rowcount
    await session.commit()
    return deleted_count
```

### Step 5: Alembic Configuration (`alembic.ini`)

```ini
# alembic.ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Database URL (override with environment variable in production)
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/oc5_ml_api

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Step 6: Alembic Environment (`alembic/env.py`)

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

# Import your models' Base
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from oc5_ml_deployment.database.models import Base

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your models' metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode (async)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Step 7: Initial Migration

```python
# alembic/versions/001_20251119_1200_initial_schema.py
"""Initial schema

Revision ID: abc123def456
Revises:
Create Date: 2025-11-19 12:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123def456'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create api_requests table
    op.create_table(
        'api_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('request_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for api_requests
    op.create_index('idx_api_requests_created_at', 'api_requests', ['created_at'])
    op.create_index('idx_api_requests_endpoint', 'api_requests', ['endpoint'])
    op.create_index('idx_api_requests_http_status', 'api_requests', ['http_status'])

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('attrition_prob', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=10), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('features_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint('attrition_prob >= 0 AND attrition_prob <= 1', name='check_attrition_prob_range'),
        sa.CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name='check_risk_level_values'),
        sa.ForeignKeyConstraint(['request_id'], ['api_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for predictions
    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'])
    op.create_index('idx_predictions_request_id', 'predictions', ['request_id'])
    op.create_index('idx_predictions_risk_level', 'predictions', ['risk_level'])
    op.create_index('idx_predictions_model_version', 'predictions', ['model_version'])
    op.create_index('idx_predictions_employee_id', 'predictions', ['employee_id'])


def downgrade() -> None:
    # Drop tables (reverse order due to FK constraint)
    op.drop_table('predictions')
    op.drop_table('api_requests')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
```

### Step 8: Integrate with FastAPI

```python
# src/oc5_ml_deployment/api/main.py
from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import time

from ..database.database import get_db
from ..database import crud
from .schemas import PredictionRequest, PredictionResponse

app = FastAPI()


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Middleware to log all API requests to database."""
    start_time = time.time()

    # Get request body (for POST requests)
    request_data = {}
    if request.method == "POST":
        try:
            request_data = await request.json()
        except:
            pass

    # Call the endpoint
    response = await call_next(request)

    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)

    # Log to database (in background, don't block response)
    async with AsyncSession(engine) as session:
        await crud.create_api_request(
            session=session,
            endpoint=request.url.path,
            request_data=request_data,
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            http_status=response.status_code,
            response_time_ms=response_time_ms
        )
        await session.commit()

    return response


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(
    data: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Make a prediction and store it in the database."""

    # Your existing prediction logic
    prediction_result = make_prediction(data)  # Your ML model

    # Create API request record
    api_request = await crud.create_api_request(
        session=db,
        endpoint="/api/v1/predict",
        request_data=data.dict(),
        client_ip="...",  # From request
        user_agent="...",  # From request
        http_status=200,
        response_time_ms=0  # Will be updated by middleware
    )

    # Create prediction record
    await crud.create_prediction(
        session=db,
        request_id=api_request.id,
        employee_id=data.employee_id,
        attrition_prob=prediction_result.probability,
        risk_level=prediction_result.risk_level,
        model_version="xgb_enhanced_v1.0",
        features_snapshot=data.dict()
    )

    await db.commit()

    return prediction_result


@app.get("/api/v1/analytics/risk-distribution")
async def get_risk_distribution(db: AsyncSession = Depends(get_db)):
    """Get distribution of predictions by risk level."""
    distribution = await crud.get_prediction_count_by_risk(db)
    return distribution
```

---

## Workflow Example

### Development Workflow

**1. Create your SQLAlchemy models:**
```python
# models.py
class NewTable(Base):
    __tablename__ = 'new_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

**2. Generate migration:**
```bash
alembic revision --autogenerate -m "add new_table"
```

**3. Review the migration file:**
```python
# Check alembic/versions/002_add_new_table.py
# Make sure it looks correct
```

**4. Apply migration:**
```bash
alembic upgrade head
```

**5. Verify in database:**
```bash
psql -d oc5_ml_api -c "\dt"  # List tables
```

### Production Deployment

**1. Developer creates migration locally:**
```bash
alembic revision --autogenerate -m "add feature"
git add alembic/versions/
git commit -m "Add database migration"
git push
```

**2. CI/CD runs migration on production:**
```bash
# In deployment script
alembic upgrade head
```

**3. Application starts with new schema:**
```bash
uvicorn main:app
```

---

## Best Practices

### 1. Always Use Migrations

❌ **Never do this:**
```python
# Don't create tables directly in code
Base.metadata.create_all(engine)
```

✅ **Always do this:**
```bash
# Use Alembic migrations
alembic upgrade head
```

### 2. Review Auto-Generated Migrations

Auto-generated migrations are not always perfect. Always review them!

```bash
alembic revision --autogenerate -m "my changes"
# Open the file and check it before running
cat alembic/versions/latest_file.py
```

### 3. Test Migrations Both Ways

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 4. Never Modify Applied Migrations

Once a migration is applied to production, **never modify it**. Create a new migration instead.

❌ **Don't:**
```python
# Edit alembic/versions/001_initial.py
def upgrade():
    op.create_table('users', ...)  # Don't change this!
```

✅ **Do:**
```bash
# Create a new migration
alembic revision -m "fix users table"
```

### 5. Use Transactions

SQLAlchemy sessions are transactional by default. Use them!

```python
try:
    session.add(prediction)
    session.commit()
except Exception:
    session.rollback()  # Undo changes
    raise
```

### 6. Use Dependencies in FastAPI

```python
# Good: Dependency injection
@app.post("/predict")
async def predict(db: AsyncSession = Depends(get_db)):
    # db is automatically managed
    pass

# Bad: Manual session management
@app.post("/predict")
async def predict():
    session = AsyncSessionLocal()
    try:
        # ... code ...
    finally:
        await session.close()  # Easy to forget!
```

### 7. Use Environment Variables

```python
# Don't hardcode database credentials
DATABASE_URL = os.getenv("DATABASE_URL")

# Or use pydantic settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"
```

### 8. Add Indexes Thoughtfully

```python
# Index columns used in WHERE clauses
created_at = Column(DateTime, index=True)  # If you filter by this

# Don't index everything (slows down writes)
random_field = Column(String)  # No index if never filtered
```

---

## Common Patterns

### Pattern 1: Pagination

```python
async def get_predictions_paginated(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Prediction]:
    result = await db.execute(
        select(Prediction)
        .offset(skip)
        .limit(limit)
        .order_by(Prediction.created_at.desc())
    )
    return result.scalars().all()

# Usage in FastAPI
@app.get("/predictions")
async def list_predictions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await get_predictions_paginated(db, skip, limit)
```

### Pattern 2: Filtering

```python
from sqlalchemy import and_, or_

# Multiple conditions (AND)
result = await db.execute(
    select(Prediction).filter(
        and_(
            Prediction.risk_level == "HIGH",
            Prediction.created_at > datetime(2025, 1, 1)
        )
    )
)

# Multiple conditions (OR)
result = await db.execute(
    select(Prediction).filter(
        or_(
            Prediction.risk_level == "HIGH",
            Prediction.attrition_prob > 0.8
        )
    )
)
```

### Pattern 3: Aggregations

```python
from sqlalchemy import func

# Count
count = await db.execute(select(func.count(Prediction.id)))
total = count.scalar()

# Average
avg = await db.execute(select(func.avg(Prediction.attrition_prob)))
average_prob = avg.scalar()

# Group by
result = await db.execute(
    select(
        Prediction.risk_level,
        func.count(Prediction.id),
        func.avg(Prediction.attrition_prob)
    ).group_by(Prediction.risk_level)
)
```

---

## Debugging Tips

### 1. Enable SQL Logging

```python
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Prints all SQL queries
)
```

### 2. Check Current Migration Version

```bash
alembic current
```

### 3. View Migration History

```bash
alembic history --verbose
```

### 4. Test Queries in psql

```bash
psql -d oc5_ml_api

# Test your query
SELECT * FROM predictions WHERE risk_level = 'HIGH';
```

### 5. Common Errors

**Error:** "Target database is not up to date"
```bash
# Solution: Run migrations
alembic upgrade head
```

**Error:** "Can't locate revision identified by 'xyz'"
```bash
# Solution: Check alembic_version table
psql -d oc5_ml_api -c "SELECT * FROM alembic_version;"
```

**Error:** "Table already exists"
```bash
# Solution: Mark current state as migrated
alembic stamp head
```

---

## Summary

**SQLAlchemy:**
- ORM that maps Python classes to database tables
- Write Python code instead of SQL
- Database-agnostic (works with PostgreSQL, MySQL, SQLite, etc.)
- Two parts: models (classes) and sessions (transactions)

**Alembic:**
- Version control for database schema
- Automatically generates migrations from model changes
- Apply/rollback migrations with simple commands
- Essential for team collaboration and production deployments

**Key Benefits:**
- ✅ Type safety and IDE autocomplete
- ✅ Less SQL boilerplate
- ✅ Easier testing (can use SQLite in tests)
- ✅ Version controlled schema changes
- ✅ Easy rollbacks
- ✅ Team-friendly (everyone gets same schema)

**Next Steps for Your Project:**
1. Install dependencies: `pip install sqlalchemy alembic asyncpg psycopg2-binary`
2. Create models in `database/models.py`
3. Setup Alembic: `alembic init alembic`
4. Configure `alembic/env.py` to use your models
5. Generate initial migration: `alembic revision --autogenerate -m "initial schema"`
6. Apply migration: `alembic upgrade head`
7. Integrate with FastAPI using dependency injection

---

*Ready to implement? Let me know if you have any questions!*
