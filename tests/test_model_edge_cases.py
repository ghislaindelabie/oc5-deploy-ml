"""
Tests for model service edge cases.

Tests error handling and edge cases in model_service.py to improve coverage.
"""
from pathlib import Path
from oc5_ml_deployment.api.model_service import ModelService


def test_model_service_with_invalid_path():
    """Test model service initialization with non-existent files."""
    service = ModelService(
        model_path=Path("/nonexistent/model.joblib"),
        metadata_path=Path("/nonexistent/metadata.json")
    )

    # Should fail to load
    result = service.load()

    assert result is False
    assert not service.is_loaded()


def test_get_model_info_when_not_loaded():
    """Test getting model info before model is loaded."""
    service = ModelService(
        model_path=Path("/nonexistent/model.joblib"),
        metadata_path=Path("/nonexistent/metadata.json")
    )

    # Don't load the model
    info = service.get_model_info()

    # Should return empty dict
    assert info == {}
