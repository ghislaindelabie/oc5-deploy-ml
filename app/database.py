"""
Database Configuration and Session Management

This module handles PostgreSQL connection and ORM setup.

Responsibilities:
    - Database connection configuration
    - SQLAlchemy engine creation
    - Session management
    - ORM model definitions
    - Database utilities

Database URL Format:
    postgresql://user:password@host:port/dbname

    From environment variable: DATABASE_URL
    Default for local dev: postgresql://postgres:postgres@localhost:5432/oc5_attrition

SQLAlchemy Setup:
    - Engine: create_engine(DATABASE_URL)
    - SessionLocal: sessionmaker(engine)
    - Base: declarative_base() for ORM models

ORM Models to Define:

    class Prediction(Base):
        __tablename__ = "predictions"

        id: int (primary key, auto-increment)
        input_data: JSON (all 26 employee features)
        prediction: str ("Oui" or "Non")
        probability: float (0-1)
        risk_level: str ("High"|"Medium"|"Low")
        top_risk_factors: JSON (list of strings)
        model_version: str
        created_at: datetime (default: now)

        # Optional fields:
        user_id: str (nullable)
        session_id: str (nullable)

Dependency Injection Pattern (for FastAPI):

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    Usage in endpoints:
        @app.post("/predict")
        def predict(data: EmployeeInput, db: Session = Depends(get_db)):
            # ... make prediction
            # Save to database
            db_prediction = Prediction(
                input_data=data.dict(),
                prediction=result["prediction"],
                ...
            )
            db.add(db_prediction)
            db.commit()
            db.refresh(db_prediction)

Connection Pooling:
    - pool_size: 5 (default)
    - max_overflow: 10
    - pool_pre_ping: True (check connection health)

TODO:
    - from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
    - from sqlalchemy.ext.declarative import declarative_base
    - from sqlalchemy.orm import sessionmaker
    - Import DATABASE_URL from config
    - Create engine with pool settings
    - Define Base and models
    - Implement get_db() dependency
"""

# CODE TO BE WRITTEN IN PHASE 2
