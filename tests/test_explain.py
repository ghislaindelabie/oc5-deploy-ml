"""Tests for SHAP explanation endpoint."""
import pytest


def test_explain_endpoint_success(client, valid_employee_data):
    """Test that explain endpoint returns top 5 features."""
    response = client.post("/api/v1/explain", json=valid_employee_data)

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "top_features" in data
    assert "metadata" in data

    # Check top features
    assert len(data["top_features"]) == 5
    for feature in data["top_features"]:
        assert "feature" in feature
        assert "shap_value" in feature
        assert "impact" in feature
        assert feature["impact"] in ["increases risk", "decreases risk", "neutral"]

    # Check metadata
    assert "model_version" in data["metadata"]
    assert "explanation_time_ms" in data["metadata"]
    assert "timestamp" in data["metadata"]
    assert isinstance(data["metadata"]["explanation_time_ms"], int)


def test_explain_endpoint_with_invalid_data(client):
    """Test that explain endpoint handles invalid data."""
    response = client.post(
        "/api/v1/explain",
        json={
            "employee_id": "TEST_001",
            "age": "invalid",  # Should be int
        }
    )

    assert response.status_code == 422
