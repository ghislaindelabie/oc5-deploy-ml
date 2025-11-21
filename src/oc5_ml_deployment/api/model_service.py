"""
Model Service for HR Attrition Prediction

Handles model loading, preprocessing, and prediction logic.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)


class ModelService:
    """Service for loading and using the trained model."""

    def __init__(self, model_path: Optional[Path] = None, metadata_path: Optional[Path] = None):
        """
        Initialize the model service.

        Args:
            model_path: Path to the trained model file
            metadata_path: Path to the feature metadata JSON file
        """
        self.model = None
        self.metadata = None
        self.feature_columns = None
        self.explainer = None

        # Default paths relative to project root
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent.parent / "model" / "hr_attrition_xgb_enhanced.joblib"
        if metadata_path is None:
            metadata_path = Path(__file__).parent.parent.parent.parent / "model" / "feature_metadata.json"

        self.model_path = model_path
        self.metadata_path = metadata_path

    def load(self) -> bool:
        """
        Load the model and metadata.

        Returns:
            True if loading successful, False otherwise
        """
        try:
            # Load model
            logger.info(f"Loading model from {self.model_path}")
            self.model = joblib.load(self.model_path)
            logger.info("Model loaded successfully")

            # Load metadata
            logger.info(f"Loading metadata from {self.metadata_path}")
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            logger.info("Metadata loaded successfully")

            # Extract feature information
            self._extract_feature_info()

            # Initialize SHAP explainer
            logger.info("Initializing SHAP explainer")
            # Extract the XGBoost model from the pipeline (if it's a pipeline)
            if hasattr(self.model, 'named_steps'):
                # It's a pipeline, extract the final estimator
                final_estimator = self.model.steps[-1][1]
                self.explainer = shap.TreeExplainer(final_estimator)
            else:
                # It's a raw model
                self.explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP explainer initialized successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to load model or metadata: {e}")
            return False

    def _extract_feature_info(self):
        """Extract feature column information from metadata."""
        if self.metadata is None:
            return

        # Get all features that should be in the input
        numeric_features = self.metadata["features"]["numeric"]
        categorical_features = self.metadata["features"]["categorical"]

        # Store for validation
        self.feature_columns = {
            "numeric": numeric_features,
            "categorical": categorical_features,
            "all": numeric_features + categorical_features,
        }

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None and self.metadata is not None

    def get_model_info(self) -> Dict:
        """
        Get model information.

        Returns:
            Dictionary with model metadata
        """
        if not self.is_loaded():
            return {}

        return {
            "model_version": self.metadata.get("model_version"),
            "training_date": self.metadata.get("training_date"),
            "performance_metrics": {
                "accuracy": round(self.metadata["performance_cv"]["accuracy_mean"], 3),
                "precision": round(self.metadata["performance_cv"]["precision_mean"], 3),
                "recall": round(self.metadata["performance_cv"]["recall_mean"], 3),
                "f1_score": round(self.metadata["performance_cv"]["f1_mean"], 3),
                "roc_auc": round(self.metadata["performance_cv"]["roc_auc_mean"], 3),
            },
            "features_required": {
                "numeric": self.feature_columns["numeric"],
                "categorical": self.feature_columns["categorical"],
            },
        }

    def preprocess_input(self, data: Dict) -> pd.DataFrame:
        """
        Preprocess input data for prediction.

        Args:
            data: Dictionary with employee features

        Returns:
            Preprocessed DataFrame ready for model
        """
        # Create DataFrame from input
        df = pd.DataFrame([data])

        # Ensure all required columns are present
        missing_cols = set(self.feature_columns["all"]) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Select only the columns used in training (in the correct order)
        df = df[self.feature_columns["all"]]

        return df

    def predict(self, data: Dict) -> Tuple[bool, float, float, str]:
        """
        Make a prediction for a single employee.

        Args:
            data: Dictionary with employee features

        Returns:
            Tuple of (will_leave, probability_leave, probability_stay, risk_level)
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")

        # Preprocess input
        df = self.preprocess_input(data)

        # Get prediction probabilities
        probabilities = self.model.predict_proba(df)[0]

        # probabilities[0] = probability of class 0 (staying)
        # probabilities[1] = probability of class 1 (leaving)
        prob_stay = float(probabilities[0]) * 100  # Convert to percentage
        prob_leave = float(probabilities[1]) * 100

        # Make binary prediction
        will_leave = bool(probabilities[1] >= 0.5)

        # Determine risk level
        risk_level = self._get_risk_level(prob_leave)

        return will_leave, prob_leave, prob_stay, risk_level

    def predict_batch(self, data_list: List[Dict]) -> List[Tuple[bool, float, float, str]]:
        """
        Make predictions for multiple employees.

        Args:
            data_list: List of dictionaries with employee features

        Returns:
            List of tuples (will_leave, probability_leave, probability_stay, risk_level)
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")

        results = []
        for data in data_list:
            result = self.predict(data)
            results.append(result)

        return results

    @staticmethod
    def _get_risk_level(probability_leave: float) -> str:
        """
        Determine risk level based on probability.

        Args:
            probability_leave: Probability of leaving (0-100)

        Returns:
            Risk level: "LOW", "MEDIUM", or "HIGH"
        """
        if probability_leave < 40:
            return "LOW"
        elif probability_leave < 60:
            return "MEDIUM"
        else:
            return "HIGH"

    def explain(self, data: Dict) -> List[Dict[str, float]]:
        """
        Generate SHAP explanations for a prediction.

        Returns the top 5 features that most influenced the prediction,
        with their SHAP values and contribution direction.

        Args:
            data: Dictionary with employee features

        Returns:
            List of dicts with feature names and SHAP values (top 5)
            Format: [{"feature": "age", "shap_value": 0.15, "impact": "increases risk"}, ...]
        """
        if not self.is_loaded() or self.explainer is None:
            raise RuntimeError("Model and explainer not loaded. Call load() first.")

        # Preprocess input to get the transformed features
        df = self.preprocess_input(data)

        # If model is a pipeline, transform the data through all preprocessing steps
        # to get the actual features the XGBoost model sees
        if hasattr(self.model, 'named_steps'):
            # Transform through all steps except the final estimator
            transformed_df = df
            for name, transformer in self.model.steps[:-1]:
                transformed_df = transformer.transform(transformed_df)

            # Try to get feature names from the last transformer
            feature_names = None
            if hasattr(self.model.steps[-2][1], 'get_feature_names_out'):
                try:
                    feature_names = self.model.steps[-2][1].get_feature_names_out()
                except:
                    pass

            # Convert to DataFrame with proper column names
            if not isinstance(transformed_df, pd.DataFrame):
                if feature_names is not None:
                    transformed_df = pd.DataFrame(transformed_df, columns=feature_names)
                else:
                    # Use sequential names as fallback
                    n_features = transformed_df.shape[1] if hasattr(transformed_df, 'shape') else len(transformed_df[0])
                    transformed_df = pd.DataFrame(
                        transformed_df,
                        columns=[f"feature_{i}" for i in range(n_features)]
                    )
        else:
            transformed_df = df

        # Calculate SHAP values
        shap_values = self.explainer.shap_values(transformed_df)

        # Get SHAP values for the "leave" class (class 1)
        # shap_values is typically [shap_for_class0, shap_for_class1]
        if isinstance(shap_values, list):
            shap_values_leave = shap_values[1][0]  # Class 1, first sample
        else:
            shap_values_leave = shap_values[0]  # Single output, first sample

        # Get feature names from the DataFrame columns
        feature_names = transformed_df.columns.tolist()

        # Create list of (feature, shap_value) tuples
        feature_importance = list(zip(feature_names, shap_values_leave))

        # Sort by absolute SHAP value (most important first)
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

        # Take top 5 and format output
        top_features = []
        for feature_name, shap_value in feature_importance[:5]:
            # Determine impact direction
            if shap_value > 0:
                impact = "increases risk"
            elif shap_value < 0:
                impact = "decreases risk"
            else:
                impact = "neutral"

            top_features.append({
                "feature": feature_name,
                "shap_value": round(float(shap_value), 4),
                "impact": impact
            })

        return top_features


# Global model service instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """
    Get the global model service instance.

    Returns:
        ModelService instance
    """
    global _model_service

    if _model_service is None:
        _model_service = ModelService()
        _model_service.load()

    return _model_service
