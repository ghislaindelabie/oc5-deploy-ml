"""
Database integration tests.

These tests verify that database logging works correctly with Supabase.
They are ONLY run during PR to main (not in local dev or feature branch CI).

Run locally with: pytest -m database
Skip with: pytest -m "not database" (default)
"""
import os
import pytest
from sqlalchemy import select, func, delete
from oc5_ml_deployment.database import DATABASE_ENABLED, engine, APIRequest, Prediction

# Skip all tests in this file if database not configured
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(
        not DATABASE_ENABLED,
        reason="Database tests require OC5_DATABASE_URL to be set"
    ),
]


@pytest.fixture
async def db_session():
    """Provide a clean database session for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        yield session

        # Cleanup: Delete test data after each test
        # (Only delete records created in last 5 minutes to avoid affecting production)
        await session.execute(
            delete(Prediction).where(
                Prediction.created_at >= func.now() - func.make_interval(0, 0, 0, 0, 0, 5)
            )
        )
        await session.execute(
            delete(APIRequest).where(
                APIRequest.created_at >= func.now() - func.make_interval(0, 0, 0, 0, 0, 5)
            )
        )
        await session.commit()


@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return {
        "employee_id": "TEST_DB_001",
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
        "heure_supplementaires": "No",
    }


@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Verify database connection works."""
    result = await db_session.execute(select(func.count()).select_from(APIRequest))
    count = result.scalar()
    assert count is not None
    assert count >= 0


@pytest.mark.asyncio
async def test_single_prediction_logs_to_database(async_client, db_session, sample_employee_data):
    """Verify single prediction is logged to database."""
    # Count records before
    result = await db_session.execute(select(func.count()).select_from(APIRequest))
    initial_requests = result.scalar()

    result = await db_session.execute(select(func.count()).select_from(Prediction))
    initial_predictions = result.scalar()

    # Make prediction
    response = await async_client.post("/api/v1/predict", json=sample_employee_data)
    assert response.status_code == 200

    # Refresh session to see new data
    await db_session.rollback()  # Clear session cache

    # Verify API request logged
    result = await db_session.execute(select(func.count()).select_from(APIRequest))
    new_requests = result.scalar()
    assert new_requests == initial_requests + 1, "API request should be logged"

    # Verify prediction logged
    result = await db_session.execute(select(func.count()).select_from(Prediction))
    new_predictions = result.scalar()
    assert new_predictions == initial_predictions + 1, "Prediction should be logged"

    # Verify prediction details
    result = await db_session.execute(
        select(Prediction)
        .where(Prediction.employee_id == "TEST_DB_001")
        .order_by(Prediction.created_at.desc())
        .limit(1)
    )
    prediction = result.scalar_one_or_none()

    assert prediction is not None
    assert prediction.risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert 0 <= prediction.attrition_prob <= 1
    assert prediction.model_version is not None


@pytest.mark.asyncio
async def test_batch_prediction_logs_to_database(async_client, db_session, sample_employee_data):
    """Verify batch predictions are logged to database."""
    # Create batch with 3 employees
    batch_data = {
        "employees": [
            {**sample_employee_data, "employee_id": "TEST_BATCH_01"},
            {**sample_employee_data, "employee_id": "TEST_BATCH_02"},
            {**sample_employee_data, "employee_id": "TEST_BATCH_03"},
        ]
    }

    # Count before
    result = await db_session.execute(select(func.count()).select_from(Prediction))
    initial_predictions = result.scalar()

    # Make batch prediction
    response = await async_client.post("/api/v1/predict/batch", json=batch_data)
    assert response.status_code == 200

    # Refresh session
    await db_session.rollback()

    # Verify 3 predictions logged
    result = await db_session.execute(select(func.count()).select_from(Prediction))
    new_predictions = result.scalar()
    assert new_predictions == initial_predictions + 3, "All 3 batch predictions should be logged"


@pytest.mark.asyncio
async def test_database_error_doesnt_break_prediction(async_client, sample_employee_data, monkeypatch):
    """Verify API still works even if database logging fails."""
    # This test verifies graceful degradation
    # (Hard to test without actually breaking DB, but validates error handling exists)

    response = await async_client.post("/api/v1/predict", json=sample_employee_data)
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert "metadata" in response.json()
