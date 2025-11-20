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
