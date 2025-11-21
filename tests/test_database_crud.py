"""
Tests for database CRUD operations.

This module tests database read operations to improve coverage
for database/crud.py.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from oc5_ml_deployment.database import DATABASE_ENABLED, crud, models

# Skip all tests in this file if database is not enabled
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(not DATABASE_ENABLED, reason="Database not configured"),
]


@pytest.fixture
async def sample_api_request(db_session):
    """Create a sample API request for testing."""
    api_request = await crud.create_api_request(
        session=db_session,
        endpoint="/api/v1/predict",
        request_data={"employee_id": "TEST_001"},
        client_ip="127.0.0.1",
        user_agent="pytest",
        http_status=200,
        response_time_ms=50
    )
    await db_session.commit()
    await db_session.refresh(api_request)
    return api_request


@pytest.fixture
async def sample_prediction(db_session, sample_api_request):
    """Create a sample prediction for testing."""
    prediction = await crud.create_prediction(
        session=db_session,
        request_id=sample_api_request.id,
        employee_id="TEST_001",
        attrition_prob=0.35,
        risk_level="medium",
        model_version="test_v1.0",
        features_snapshot={"age": 35, "department": "Sales"}
    )
    await db_session.commit()
    await db_session.refresh(prediction)
    return prediction


@pytest.mark.asyncio
async def test_get_api_request(db_session, sample_api_request):
    """Test retrieving an API request by ID."""
    retrieved = await crud.get_api_request(db_session, sample_api_request.id)

    assert retrieved is not None
    assert retrieved.id == sample_api_request.id
    assert retrieved.endpoint == "/api/v1/predict"
    assert retrieved.http_status == 200


@pytest.mark.asyncio
async def test_get_api_request_nonexistent(db_session):
    """Test retrieving a non-existent API request."""
    retrieved = await crud.get_api_request(db_session, 999999999)

    assert retrieved is None


@pytest.mark.asyncio
async def test_get_predictions_for_request(db_session, sample_api_request, sample_prediction):
    """Test retrieving predictions for a specific request."""
    predictions = await crud.get_predictions(
        db_session,
        request_id=sample_api_request.id
    )

    assert len(predictions) >= 1
    assert any(p.id == sample_prediction.id for p in predictions)


@pytest.mark.asyncio
async def test_get_predictions_for_employee(db_session, sample_prediction):
    """Test retrieving predictions for a specific employee."""
    predictions = await crud.get_predictions(
        db_session,
        employee_id="TEST_001"
    )

    assert len(predictions) >= 1
    assert any(p.employee_id == "TEST_001" for p in predictions)


@pytest.mark.asyncio
async def test_get_predictions_with_limit(db_session, sample_api_request):
    """Test retrieving predictions with limit."""
    # Create multiple predictions
    for i in range(5):
        await crud.create_prediction(
            session=db_session,
            request_id=sample_api_request.id,
            employee_id=f"TEST_{i:03d}",
            attrition_prob=0.3 + (i * 0.1),
            risk_level="medium",
            model_version="test_v1.0",
            features_snapshot={"age": 30 + i}
        )
    await db_session.commit()

    # Get only 3 predictions
    predictions = await crud.get_predictions(db_session, limit=3)

    assert len(predictions) <= 3


@pytest.mark.asyncio
async def test_get_predictions_with_date_range(db_session, sample_api_request):
    """Test retrieving predictions within a date range."""
    now = datetime.utcnow()

    # Create prediction with current timestamp
    prediction = await crud.create_prediction(
        session=db_session,
        request_id=sample_api_request.id,
        employee_id="TEST_DATE",
        attrition_prob=0.4,
        risk_level="medium",
        model_version="test_v1.0",
        features_snapshot={"age": 40}
    )
    await db_session.commit()

    # Query with date range that includes the prediction
    start_date = now - timedelta(minutes=5)
    end_date = now + timedelta(minutes=5)

    predictions = await crud.get_predictions(
        db_session,
        start_date=start_date,
        end_date=end_date
    )

    # Should find at least our test prediction
    assert len(predictions) >= 1
    assert any(p.employee_id == "TEST_DATE" for p in predictions)
