"""
Database package for OC5 ML Deployment.

Provides database models, connection management, and CRUD operations.
"""

from .database import Base, engine, get_db, DATABASE_ENABLED
from .models import APIRequest, Prediction

__all__ = ["Base", "engine", "get_db", "DATABASE_ENABLED", "APIRequest", "Prediction"]
