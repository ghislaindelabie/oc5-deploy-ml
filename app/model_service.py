"""
Model Service - Model Loading and Prediction Logic

This module handles:
    - Loading the trained model pipeline on startup
    - Converting API input to model format
    - Making predictions
    - Extracting feature importance / risk factors
    - Error handling for model failures

Key Functions:

    load_model() -> Pipeline:
        - Load model/hr_attrition_xgb_enhanced.joblib
        - Load model/feature_metadata.json
        - Validate model loaded correctly
        - Return pipeline object
        - Called ONCE on FastAPI startup (lifespan event)

    predict(employee_data: dict, model: Pipeline) -> dict:
        - Convert employee_data dict to pandas DataFrame
        - Ensure correct feature order (26 features)
        - Call model.predict() and model.predict_proba()
        - Extract probability of class 1 (leaving)
        - Determine risk level (High/Medium/Low)
        - Return dict with prediction results

    get_top_risk_factors(employee_data: dict, model: Pipeline) -> List[str]:
        - Extract feature importance from XGBoost
        - Identify which high-importance features are "risky" in this input
        - Return top 3 factors as human-readable strings
        - Alternative: use SHAP if time permits (optional)

    validate_feature_order(df: pd.DataFrame) -> pd.DataFrame:
        - Ensure columns match training order
        - Reorder if necessary
        - Raise error if features missing

Model Loading Pattern (FastAPI lifespan):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load model on startup
        app.state.model = load_model()
        yield
        # Cleanup on shutdown (if needed)

Error Handling:
    - ModelNotFoundError: if joblib file missing
    - PredictionError: if model.predict() fails
    - FeatureValidationError: if input features don't match

TODO:
    - Import joblib, pandas, numpy
    - Import Pipeline from sklearn
    - Implement load_model()
    - Implement predict()
    - Implement get_top_risk_factors()
    - Add logging for debugging
"""

# CODE TO BE WRITTEN IN PHASE 1
