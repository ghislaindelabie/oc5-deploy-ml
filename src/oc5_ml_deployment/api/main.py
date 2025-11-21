"""
FastAPI Application for HR Attrition Prediction

Provides REST API endpoints for predicting employee attrition using
a trained XGBoost model.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .model_service import get_model_service
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    BatchPredictionItem,
    EmployeeFeatures,
    HealthResponse,
    ModelInfoResponse,
    PredictionResponse,
    PredictionResult,
)

# Import database components (optional - works without database)
from ..database import get_db, DATABASE_ENABLED
from ..database import crud

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting up API...")

    # Check model
    model_service = get_model_service()
    if model_service.is_loaded():
        logger.info("Model loaded successfully")
    else:
        logger.error("Failed to load model")

    # Check database
    if DATABASE_ENABLED:
        logger.info("Database logging is ENABLED")
    else:
        logger.warning("Database logging is DISABLED - predictions will not be saved")

    yield

    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="HR Attrition Prediction API",
    description="REST API for predicting employee attrition using machine learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Path to static HTML landing page
LANDING_PAGE_PATH = Path(__file__).parent / "static" / "landing.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    Serve the landing page with API overview.

    Provides a user-friendly HTML page displaying:
    - API status and health
    - Available endpoints with descriptions
    - Links to interactive documentation (/docs, /redoc)
    - GitHub repository link

    Falls back to redirecting to /docs if landing page is not available.

    Returns:
        HTMLResponse: Rendered landing page with caching headers
        RedirectResponse: Redirect to /docs if landing page is missing
    """
    try:
        html_content = LANDING_PAGE_PATH.read_text(encoding="utf-8")
        return HTMLResponse(
            content=html_content,
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    except FileNotFoundError:
        # Graceful fallback if landing page is missing (e.g., packaging issue)
        logger.warning(
            f"Landing page not found at {LANDING_PAGE_PATH}. "
            "Redirecting to API documentation."
        )
        return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Check API health and model status.

    Returns health status, model loading state, and version information.
    """
    model_service = get_model_service()
    is_loaded = model_service.is_loaded()

    model_version = None
    if is_loaded and model_service.metadata:
        model_version = model_service.metadata.get("model_version")

    return HealthResponse(
        status="healthy" if is_loaded else "unhealthy",
        model_loaded=is_loaded,
        model_version=model_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/api/v1/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """
    Get model information and metadata.

    Returns model version, training date, performance metrics,
    and required features.
    """
    model_service = get_model_service()

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    info = model_service.get_model_info()

    return ModelInfoResponse(**info)


@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict_single(
    employee: EmployeeFeatures,
    request: Request,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """
    Predict attrition for a single employee.

    Accepts employee features and returns prediction with probability
    and risk level. Logs request and prediction to database if enabled.

    Args:
        employee: Employee features
        request: FastAPI request object (for metadata)
        db: Database session (optional, depends on DATABASE_ENABLED)

    Returns:
        Prediction result with probabilities and metadata
    """
    model_service = get_model_service()

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    start_time = time.time()
    http_status_code = status.HTTP_200_OK

    try:
        # Convert Pydantic model to dict
        employee_data = employee.model_dump()

        # Make prediction
        will_leave, prob_leave, prob_stay, risk_level = model_service.predict(employee_data)

        # Calculate prediction time
        prediction_time_ms = int((time.time() - start_time) * 1000)

        # Log to database if enabled
        if DATABASE_ENABLED and db is not None:
            try:
                # Create API request record
                api_request = await crud.create_api_request(
                    session=db,
                    endpoint="/api/v1/predict",
                    request_data=employee_data,
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    http_status=http_status_code,
                    response_time_ms=prediction_time_ms
                )

                # Create prediction record
                await crud.create_prediction(
                    session=db,
                    request_id=api_request.id,
                    employee_id=employee_data.get("employee_id"),
                    attrition_prob=prob_leave,
                    risk_level=risk_level,
                    model_version=model_service.metadata.get("model_version"),
                    features_snapshot=employee_data
                )

                # Commit handled by get_db() dependency
                logger.debug(f"Logged prediction to database: request_id={api_request.id}")
            except Exception as db_error:
                logger.error(f"Failed to log to database: {db_error}")
                # Don't fail the request if database logging fails
                # Must rollback here since we're suppressing the exception
                await db.rollback()

        # Build response
        return PredictionResponse(
            prediction=PredictionResult(
                will_leave=will_leave,
                probability_leave=round(prob_leave, 2),
                probability_stay=round(prob_stay, 2),
                risk_level=risk_level,
            ),
            metadata={
                "model_version": model_service.metadata.get("model_version"),
                "prediction_time_ms": prediction_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    except ValueError as e:
        http_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=http_status_code, detail=str(e))
    except Exception as e:
        http_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=http_status_code, detail="Failed to generate prediction")


@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch(
    batch_request: BatchPredictionRequest,
    request: Request,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """
    Predict attrition for multiple employees.

    Accepts a list of employees (up to 100) and returns predictions
    for each one. Logs all requests and predictions to database if enabled.

    Args:
        batch_request: Batch prediction request with list of employees
        request: FastAPI request object (for metadata)
        db: Database session (optional, depends on DATABASE_ENABLED)

    Returns:
        Batch prediction results with metadata
    """
    model_service = get_model_service()

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    start_time = time.time()
    http_status_code = status.HTTP_200_OK

    try:
        # Extract employee data
        employees_data = []
        employee_ids = []

        for employee in batch_request.employees:
            employee_dict = employee.model_dump()
            employee_id = employee_dict.pop("employee_id")
            employee_ids.append(employee_id)
            employees_data.append(employee_dict)

        # Make batch predictions
        predictions = model_service.predict_batch(employees_data)

        # Calculate prediction time
        prediction_time_ms = int((time.time() - start_time) * 1000)

        # Log to database if enabled
        api_request_id = None
        if DATABASE_ENABLED and db is not None:
            try:
                # Create API request record (one for the whole batch)
                api_request = await crud.create_api_request(
                    session=db,
                    endpoint="/api/v1/predict/batch",
                    request_data={"employee_count": len(employees_data)},
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    http_status=http_status_code,
                    response_time_ms=prediction_time_ms
                )
                api_request_id = api_request.id

                # Create prediction records (one for each employee)
                for employee_id, employee_data, (will_leave, prob_leave, prob_stay, risk_level) in zip(
                    employee_ids, employees_data, predictions
                ):
                    await crud.create_prediction(
                        session=db,
                        request_id=api_request.id,
                        employee_id=employee_id,
                        attrition_prob=prob_leave,
                        risk_level=risk_level,
                        model_version=model_service.metadata.get("model_version"),
                        features_snapshot=employee_data
                    )

                # Commit handled by get_db() dependency
                logger.debug(f"Logged batch predictions to database: request_id={api_request.id}, count={len(predictions)}")
            except Exception as db_error:
                logger.error(f"Failed to log batch to database: {db_error}")
                # Don't fail the request if database logging fails
                # Must rollback here since we're suppressing the exception
                await db.rollback()

        # Build response
        prediction_items = []
        for employee_id, (will_leave, prob_leave, prob_stay, risk_level) in zip(employee_ids, predictions):
            prediction_items.append(
                BatchPredictionItem(
                    employee_id=employee_id,
                    will_leave=will_leave,
                    probability_leave=round(prob_leave, 2),
                    risk_level=risk_level,
                )
            )

        return BatchPredictionResponse(
            predictions=prediction_items,
            metadata={
                "total_predictions": len(prediction_items),
                "model_version": model_service.metadata.get("model_version"),
                "prediction_time_ms": prediction_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    except ValueError as e:
        http_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=http_status_code, detail=str(e))
    except Exception as e:
        http_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=http_status_code, detail="Failed to generate batch predictions")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
