"""
CRUD operations for database (Create, Read, Update, Delete).

Minimal implementation with only operations needed for v1.0.0:
- Create API request
- Create prediction
- Cleanup old data (365-day retention)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from .models import APIRequest, Prediction

logger = logging.getLogger(__name__)


# ============================================================================
# CREATE Operations
# ============================================================================

async def create_api_request(
    session: AsyncSession,
    endpoint: str,
    request_data: dict,
    client_ip: Optional[str],
    user_agent: Optional[str],
    http_status: int,
    response_time_ms: int
) -> APIRequest:
    """
    Create a new API request record.

    Args:
        session: Database session
        endpoint: API endpoint path (e.g., "/api/v1/predict")
        request_data: Full request payload (JSON)
        client_ip: Client IP address (IPv4 or IPv6)
        user_agent: HTTP User-Agent header
        http_status: HTTP response status code (e.g., 200, 422, 500)
        response_time_ms: Request processing time in milliseconds

    Returns:
        APIRequest: Created request object with generated ID
    """
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
    logger.debug(f"Created API request: {request.id} - {endpoint}")
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
    """
    Create a new prediction record.

    Args:
        session: Database session
        request_id: Foreign key to API request
        employee_id: Employee ID from request (optional)
        attrition_prob: Predicted attrition probability (0-1)
        risk_level: Risk category (LOW, MEDIUM, HIGH)
        model_version: Model version used (e.g., "xgb_enhanced_v1.0")
        features_snapshot: Preprocessed features (optional, for future analysis)

    Returns:
        Prediction: Created prediction object with generated ID
    """
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
    logger.debug(f"Created prediction: {prediction.id} - Risk: {risk_level}, Prob: {attrition_prob:.2f}")
    return prediction


# ============================================================================
# DELETE Operations (Data Retention)
# ============================================================================

async def cleanup_old_data(session: AsyncSession, retention_days: int = 365) -> int:
    """
    Delete API requests and predictions older than retention period.

    This implements the 365-day data retention policy. Predictions are
    automatically deleted via CASCADE when their parent request is deleted.

    Args:
        session: Database session
        retention_days: Number of days to retain data (default: 365)

    Returns:
        int: Number of API requests deleted

    Note: Should be run as a scheduled job (e.g., daily at 2 AM UTC)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    # Delete old requests (predictions will cascade)
    result = await session.execute(
        delete(APIRequest).where(APIRequest.created_at < cutoff_date)
    )

    deleted_count = result.rowcount
    await session.commit()

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} API requests older than {retention_days} days")
    else:
        logger.debug(f"No data to clean up (retention: {retention_days} days)")

    return deleted_count


# ============================================================================
# FUTURE OPERATIONS (Planned for v1.1.0+)
# ============================================================================
# When implementing analytics endpoints, add:
# - get_high_risk_predictions(session, days=30)
# - get_prediction_count_by_risk(session)
# - get_average_attrition_prob(session)
# - get_predictions_by_employee(session, employee_id)
