"""
FastAPI Application for HR Attrition Prediction

Provides REST API endpoints for predicting employee attrition using
a trained XGBoost model.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse

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
    model_service = get_model_service()
    if model_service.is_loaded():
        logger.info("Model loaded successfully")
    else:
        logger.error("Failed to load model")

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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    Landing page with API information and links.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HR Attrition Prediction API</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                color: #2d3748;
                font-size: 2.5rem;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            .header p {
                color: #718096;
                font-size: 1.1rem;
            }
            .status-badge {
                display: inline-block;
                background: #48bb78;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: 600;
                margin: 20px 0;
            }
            .endpoints {
                margin: 30px 0;
            }
            .endpoint-card {
                background: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .endpoint-card:hover {
                transform: translateX(5px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            }
            .endpoint-card h3 {
                color: #2d3748;
                margin-bottom: 8px;
                font-size: 1.2rem;
            }
            .endpoint-card p {
                color: #718096;
                margin-bottom: 10px;
            }
            .endpoint-link {
                display: inline-block;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                font-family: 'Courier New', monospace;
                font-size: 0.95rem;
            }
            .endpoint-link:hover {
                text-decoration: underline;
            }
            .method-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 700;
                margin-right: 8px;
            }
            .method-get {
                background: #bee3f8;
                color: #2c5282;
            }
            .method-post {
                background: #c6f6d5;
                color: #22543d;
            }
            .cta-section {
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
            }
            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border-radius: 30px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
                transition: transform 0.2s, box-shadow 0.2s;
                margin: 10px;
            }
            .cta-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #a0aec0;
                font-size: 0.9rem;
            }
            @media (max-width: 600px) {
                .header h1 {
                    font-size: 1.8rem;
                }
                .container {
                    padding: 25px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 HR Attrition Prediction API</h1>
                <p>Machine Learning powered employee attrition risk assessment</p>
                <span class="status-badge">🟢 API Online</span>
            </div>

            <div class="endpoints">
                <div class="endpoint-card">
                    <h3>
                        <span class="method-badge method-get">GET</span>
                        Health Check
                    </h3>
                    <p>Check API status and model availability</p>
                    <a href="/health" class="endpoint-link" target="_blank">/health</a>
                </div>

                <div class="endpoint-card">
                    <h3>
                        <span class="method-badge method-get">GET</span>
                        Model Information
                    </h3>
                    <p>Get model version, performance metrics, and required features</p>
                    <a href="/api/v1/model/info" class="endpoint-link" target="_blank">/api/v1/model/info</a>
                </div>

                <div class="endpoint-card">
                    <h3>
                        <span class="method-badge method-post">POST</span>
                        Single Prediction
                    </h3>
                    <p>Predict attrition risk for a single employee</p>
                    <span class="endpoint-link">/api/v1/predict</span>
                </div>

                <div class="endpoint-card">
                    <h3>
                        <span class="method-badge method-post">POST</span>
                        Batch Prediction
                    </h3>
                    <p>Predict attrition risk for multiple employees (up to 100)</p>
                    <span class="endpoint-link">/api/v1/predict/batch</span>
                </div>
            </div>

            <div class="cta-section">
                <a href="/docs" class="cta-button">📚 Interactive API Documentation</a>
                <a href="/redoc" class="cta-button">📖 ReDoc Documentation</a>
            </div>

            <div class="footer">
                <p>Built with FastAPI • XGBoost • Deployed on Hugging Face Spaces</p>
                <p style="margin-top: 10px;">
                    <a href="https://github.com/ghislaindelabie/oc5-deploy-ml"
                       style="color: #667eea; text-decoration: none;">
                        View on GitHub
                    </a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
async def predict_single(employee: EmployeeFeatures):
    """
    Predict attrition for a single employee.

    Accepts employee features and returns prediction with probability
    and risk level.

    Args:
        employee: Employee features

    Returns:
        Prediction result with probabilities and metadata
    """
    model_service = get_model_service()

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    try:
        # Convert Pydantic model to dict
        employee_data = employee.model_dump()

        # Start timing
        start_time = time.time()

        # Make prediction
        will_leave, prob_leave, prob_stay, risk_level = model_service.predict(employee_data)

        # Calculate prediction time
        prediction_time_ms = int((time.time() - start_time) * 1000)

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
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate prediction"
        )


@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict attrition for multiple employees.

    Accepts a list of employees (up to 100) and returns predictions
    for each one.

    Args:
        request: Batch prediction request with list of employees

    Returns:
        Batch prediction results with metadata
    """
    model_service = get_model_service()

    if not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )

    try:
        # Start timing
        start_time = time.time()

        # Extract employee data
        employees_data = []
        employee_ids = []

        for employee in request.employees:
            employee_dict = employee.model_dump()
            employee_id = employee_dict.pop("employee_id")
            employee_ids.append(employee_id)
            employees_data.append(employee_dict)

        # Make batch predictions
        predictions = model_service.predict_batch(employees_data)

        # Calculate prediction time
        prediction_time_ms = int((time.time() - start_time) * 1000)

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
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch predictions"
        )


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
