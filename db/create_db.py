"""
Database Creation and Setup Script (Python alternative to schema.sql)

This script creates the database and tables using SQLAlchemy.
Alternative to running schema.sql manually.

Purpose:
    - Create PostgreSQL database if it doesn't exist
    - Create all tables defined in app/database.py
    - Create indexes
    - Insert sample data for testing (optional)

Usage:
    python db/create_db.py

Prerequisites:
    - PostgreSQL server running
    - Database credentials in .env or environment variables
    - DATABASE_URL configured

Steps:
    1. Connect to PostgreSQL server (postgres database)
    2. Check if target database exists
    3. Create database if missing: CREATE DATABASE oc5_attrition
    4. Connect to target database
    5. Create tables using Base.metadata.create_all(engine)
    6. Create indexes
    7. Optionally insert sample prediction records for testing

Connection Patterns:

    # Connect to postgres db to create target db
    admin_engine = create_engine('postgresql://user:pass@host/postgres')

    # Connect to target db to create tables
    app_engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(app_engine)

Error Handling:
    - Database already exists: skip creation
    - Tables already exist: skip (no error)
    - Connection failures: print helpful message with troubleshooting

Sample Data (optional):
    - 5-10 example predictions with varied risk levels
    - Use for testing API without making live predictions

TODO:
    - Import sqlalchemy, psycopg2
    - Import Base, Prediction from app.database
    - Implement database creation logic
    - Implement table creation
    - Add sample data insertion function
    - Add command-line arguments (--reset, --sample-data)
"""

# CODE TO BE WRITTEN IN PHASE 2
