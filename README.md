# OC5 — Déployez un modèle de Machine Learning

Production-ready ML deployment for HR attrition prediction.

## Project Overview

This project implements a complete machine learning pipeline for predicting employee attrition, including:
- XGBoost model training with cross-validation
- FastAPI REST API for predictions
- CI/CD pipeline with GitHub Actions
- Deployment to Hugging Face Spaces

## Quickstart

```bash
# Option A: venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run API locally
uvicorn src.oc5_ml_deployment.api.main:app --reload

# Run tests
pytest
```

## API Endpoints

The API provides the following endpoints:

### Health Check
- `GET /health` - Check API and model status

### Model Information
- `GET /api/v1/model/info` - Get model metadata and performance metrics

### Predictions
- `POST /api/v1/predict` - Single employee prediction
- `POST /api/v1/predict/batch` - Batch predictions (up to 100 employees)

See the `/docs` endpoint (Swagger UI) when running the API for detailed schema documentation.

## API Design Decisions

### Rate Limiting
**Note**: This version intentionally does NOT implement rate limiting for the following reasons:
- This is a portfolio/educational project with limited traffic
- Hugging Face Spaces already provides infrastructure-level resource limits
- Rate limiting adds unnecessary complexity for the current use case
- Can be easily added later if needed using libraries like `slowapi` or `fastapi-limiter`

If you need to add rate limiting in production, consider:
- Per-IP rate limits (e.g., 100 requests/minute)
- Per-user API key limits
- Different limits for single vs. batch predictions

### Authentication
Currently no authentication is implemented. For production use, consider adding:
- API key authentication
- OAuth2/JWT tokens
- Role-based access control

## Model Training

To retrain the model:

```bash
python scripts/train_model.py
