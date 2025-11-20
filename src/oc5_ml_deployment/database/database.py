"""
Database connection and session management.

Provides async database engine and session factory for PostgreSQL.
"""

import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# Get database URL from environment variable
# For app connections (with connection pooling via pgbouncer)
DATABASE_URL = os.getenv("OC5_DATABASE_URL")

# Check if database is configured
DATABASE_ENABLED = DATABASE_URL is not None

if DATABASE_ENABLED:
    logger.info("Database is enabled")

    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # Set to True to see SQL queries (debugging)
        pool_size=5,  # Number of permanent connections
        max_overflow=10,  # Additional connections when pool is full
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "statement_cache_size": 0,  # Disable prepared statements for pgbouncer compatibility
        },
    )

    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
    )

    logger.info(f"Database engine created for: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
else:
    logger.warning(
        "Database is DISABLED - OC5_DATABASE_URL not set. "
        "Prediction requests will not be logged."
    )
    engine = None
    AsyncSessionLocal = None


# Base class for models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide database session to FastAPI routes.

    Usage in FastAPI:
        @app.post("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass

    Yields:
        AsyncSession: Database session

    Note: Session is automatically committed on success and rolled back on error.
    """
    if not DATABASE_ENABLED:
        # Return None if database is not configured
        # Endpoints should handle None gracefully
        yield None
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
