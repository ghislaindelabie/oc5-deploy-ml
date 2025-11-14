"""
Integration Tests for FastAPI Endpoints

Tests the complete API functionality including model loading,
predictions, and error handling.
"""

import pytest
from fastapi.testclient import TestClient

from oc5_ml_deployment.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_employee_data():
    """Valid employee data for testing predictions."""
    return {
        "age": 35,
        "revenu_mensuel": 5000.0,
        "nombre_experiences_precedentes": 3,
        "nombre_heures_travailless": 40,
        "annees_dans_le_poste_actuel": 2,
        "satisfaction_employee_environnement": 4,
        "note_evaluation_precedente": 3,
        "satisfaction_employee_nature_travail": 4,
        "satisfaction_employee_equipe": 3,
        "satisfaction_employee_equilibre_pro_perso": 3,
        "note_evaluation_actuelle": 3,
        "nombre_participation_pee": 1,
        "nb_formations_suivies": 2,
        "nombre_employee_sous_responsabilite": 0,
        "distance_domicile_travail": 10,
        "niveau_education": 3,
        "annees_depuis_la_derniere_promotion": 1,
        "annes_sous_responsable_actuel": 2,
        "genre": "Male",
        "statut_marital": "Married",
        "departement": "Sales",
        "poste": "Sales Executive",
        "domaine_etude": "Life Sciences",
        "heure_supplementaires": "No",
    }


# ===== Health Endpoint Tests =====


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Health response should have correct format."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "model_loaded" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["model_loaded"], bool)

    def test_health_shows_model_loaded(self, client):
        """Health should indicate model is loaded."""
        response = client.get("/health")
        data = response.json()

        assert data["model_loaded"] is True
        assert data["status"] == "healthy"
        assert data["model_version"] is not None


# ===== Model Info Endpoint Tests =====


class TestModelInfoEndpoint:
    """Tests for the model info endpoint."""

    def test_model_info_returns_200(self, client):
        """Model info endpoint should return 200."""
        response = client.get("/api/v1/model/info")
        assert response.status_code == 200

    def test_model_info_response_format(self, client):
        """Model info should have correct structure."""
        response = client.get("/api/v1/model/info")
        data = response.json()

        assert "model_version" in data
        assert "training_date" in data
        assert "performance_metrics" in data
        assert "features_required" in data

    def test_model_info_includes_performance_metrics(self, client):
        """Model info should include performance metrics."""
        response = client.get("/api/v1/model/info")
        data = response.json()

        metrics = data["performance_metrics"]
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert "roc_auc" in metrics

        # Check metrics are reasonable (between 0 and 1)
        assert 0 <= metrics["accuracy"] <= 1
        assert 0 <= metrics["precision"] <= 1
        assert 0 <= metrics["recall"] <= 1

    def test_model_info_includes_feature_lists(self, client):
        """Model info should list required features."""
        response = client.get("/api/v1/model/info")
        data = response.json()

        features = data["features_required"]
        assert "numeric" in features
        assert "categorical" in features
        assert isinstance(features["numeric"], list)
        assert isinstance(features["categorical"], list)
        assert len(features["numeric"]) > 0
        assert len(features["categorical"]) > 0


# ===== Single Prediction Endpoint Tests =====


class TestPredictEndpoint:
    """Tests for single prediction endpoint."""

    def test_predict_valid_input_returns_200(self, client, valid_employee_data):
        """Valid prediction request should return 200."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        assert response.status_code == 200

    def test_predict_response_format(self, client, valid_employee_data):
        """Prediction response should have correct format."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        assert "prediction" in data
        assert "metadata" in data

        prediction = data["prediction"]
        assert "will_leave" in prediction
        assert "probability_leave" in prediction
        assert "probability_stay" in prediction
        assert "risk_level" in prediction

    def test_predict_probabilities_are_percentages(self, client, valid_employee_data):
        """Probabilities should be in percentage format (0-100)."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        prediction = data["prediction"]
        prob_leave = prediction["probability_leave"]
        prob_stay = prediction["probability_stay"]

        assert 0 <= prob_leave <= 100
        assert 0 <= prob_stay <= 100

    def test_predict_risk_level_is_valid(self, client, valid_employee_data):
        """Risk level should be low, medium, or high."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        risk_level = data["prediction"]["risk_level"]
        assert risk_level in ["low", "medium", "high"]

    def test_predict_includes_metadata(self, client, valid_employee_data):
        """Response should include prediction metadata."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        metadata = data["metadata"]
        assert "model_version" in metadata
        assert "prediction_time_ms" in metadata
        assert "timestamp" in metadata
        assert isinstance(metadata["prediction_time_ms"], int)

    def test_predict_missing_fields_returns_422(self, client):
        """Request with missing fields should return 422."""
        incomplete_data = {"age": 35}
        response = client.post("/api/v1/predict", json=incomplete_data)
        assert response.status_code == 422

    def test_predict_invalid_age_returns_422(self, client, valid_employee_data):
        """Invalid age should return 422."""
        invalid_data = valid_employee_data.copy()
        invalid_data["age"] = 17  # Below minimum

        response = client.post("/api/v1/predict", json=invalid_data)
        assert response.status_code == 422

    def test_predict_invalid_genre_returns_422(self, client, valid_employee_data):
        """Invalid gender should return 422."""
        invalid_data = valid_employee_data.copy()
        invalid_data["genre"] = "Unknown"

        response = client.post("/api/v1/predict", json=invalid_data)
        assert response.status_code == 422

    def test_predict_negative_salary_returns_422(self, client, valid_employee_data):
        """Negative salary should return 422."""
        invalid_data = valid_employee_data.copy()
        invalid_data["revenu_mensuel"] = -1000

        response = client.post("/api/v1/predict", json=invalid_data)
        assert response.status_code == 422

    def test_predict_consistency(self, client, valid_employee_data):
        """Same input should produce same prediction."""
        response1 = client.post("/api/v1/predict", json=valid_employee_data)
        response2 = client.post("/api/v1/predict", json=valid_employee_data)

        data1 = response1.json()
        data2 = response2.json()

        assert data1["prediction"]["will_leave"] == data2["prediction"]["will_leave"]
        assert data1["prediction"]["probability_leave"] == data2["prediction"]["probability_leave"]


# ===== Batch Prediction Endpoint Tests =====


class TestBatchPredictEndpoint:
    """Tests for batch prediction endpoint."""

    def test_batch_predict_valid_input_returns_200(self, client, valid_employee_data):
        """Valid batch prediction request should return 200."""
        batch_data = {
            "employees": [
                {"employee_id": "EMP001", **valid_employee_data},
                {"employee_id": "EMP002", **valid_employee_data},
            ]
        }

        response = client.post("/api/v1/predict/batch", json=batch_data)
        assert response.status_code == 200

    def test_batch_predict_response_format(self, client, valid_employee_data):
        """Batch response should have correct format."""
        batch_data = {
            "employees": [
                {"employee_id": "EMP001", **valid_employee_data},
            ]
        }

        response = client.post("/api/v1/predict/batch", json=batch_data)
        data = response.json()

        assert "predictions" in data
        assert "metadata" in data
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 1

    def test_batch_predict_includes_employee_ids(self, client, valid_employee_data):
        """Batch predictions should include employee IDs."""
        batch_data = {
            "employees": [
                {"employee_id": "EMP001", **valid_employee_data},
                {"employee_id": "EMP002", **valid_employee_data},
            ]
        }

        response = client.post("/api/v1/predict/batch", json=batch_data)
        data = response.json()

        predictions = data["predictions"]
        assert predictions[0]["employee_id"] == "EMP001"
        assert predictions[1]["employee_id"] == "EMP002"

    def test_batch_predict_multiple_employees(self, client, valid_employee_data):
        """Batch should handle multiple different employees."""
        employee1 = valid_employee_data.copy()
        employee2 = valid_employee_data.copy()
        employee2["age"] = 25
        employee2["satisfaction_employee_environnement"] = 1

        batch_data = {
            "employees": [
                {"employee_id": "EMP001", **employee1},
                {"employee_id": "EMP002", **employee2},
            ]
        }

        response = client.post("/api/v1/predict/batch", json=batch_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["predictions"]) == 2
        assert data["metadata"]["total_predictions"] == 2

    def test_batch_predict_empty_list_returns_422(self, client):
        """Empty employee list should return 422."""
        batch_data = {"employees": []}

        response = client.post("/api/v1/predict/batch", json=batch_data)
        assert response.status_code == 422

    def test_batch_predict_missing_employee_id_returns_422(self, client, valid_employee_data):
        """Batch item without employee_id should return 422."""
        batch_data = {"employees": [valid_employee_data]}  # Missing employee_id

        response = client.post("/api/v1/predict/batch", json=batch_data)
        assert response.status_code == 422


# ===== Edge Cases and Integration Tests =====


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_predict_with_minimum_values(self, client, valid_employee_data):
        """Test prediction with minimum allowed values."""
        min_data = valid_employee_data.copy()
        min_data.update({
            "age": 18,
            "revenu_mensuel": 0.01,
            "satisfaction_employee_environnement": 1,
            "note_evaluation_actuelle": 1,
        })

        response = client.post("/api/v1/predict", json=min_data)
        assert response.status_code == 200

    def test_predict_with_maximum_values(self, client, valid_employee_data):
        """Test prediction with maximum allowed values."""
        max_data = valid_employee_data.copy()
        max_data.update({
            "age": 70,
            "satisfaction_employee_environnement": 5,
            "note_evaluation_actuelle": 4,
        })

        response = client.post("/api/v1/predict", json=max_data)
        assert response.status_code == 200

    def test_predict_with_special_characters(self, client, valid_employee_data):
        """Test that special characters in text fields are handled."""
        special_data = valid_employee_data.copy()
        special_data.update({
            "poste": "Développeur Sénior",
            "departement": "Recherche & Développement",
            "domaine_etude": "Sciences de l'ingénieur",
        })

        response = client.post("/api/v1/predict", json=special_data)
        assert response.status_code == 200

    def test_predict_with_french_categorical_values(self, client, valid_employee_data):
        """Test with French categorical value variants."""
        french_data = valid_employee_data.copy()
        french_data.update({
            "genre": "Homme",
            "statut_marital": "Marié",
        })

        response = client.post("/api/v1/predict", json=french_data)
        assert response.status_code == 200

    def test_risk_level_categorization(self, client, valid_employee_data):
        """Test that risk levels are properly categorized."""
        # Create different employee profiles that should have different risk levels
        # Note: Actual predictions depend on the model, but we can verify the mapping works

        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        prob = data["prediction"]["probability_leave"]
        risk = data["prediction"]["risk_level"]

        # Verify risk level matches probability
        if prob < 40:
            assert risk == "low"
        elif prob < 60:
            assert risk == "medium"
        else:
            assert risk == "high"


# ===== Performance Tests =====


class TestPerformance:
    """Test API performance characteristics."""

    def test_prediction_time_is_reasonable(self, client, valid_employee_data):
        """Prediction should complete in reasonable time."""
        response = client.post("/api/v1/predict", json=valid_employee_data)
        data = response.json()

        prediction_time = data["metadata"]["prediction_time_ms"]
        assert prediction_time < 1000  # Should be under 1 second

    def test_batch_prediction_time_scales(self, client, valid_employee_data):
        """Batch predictions should be reasonably fast."""
        batch_data = {
            "employees": [
                {"employee_id": f"EMP{i:03d}", **valid_employee_data}
                for i in range(10)
            ]
        }

        response = client.post("/api/v1/predict/batch", json=batch_data)
        data = response.json()

        prediction_time = data["metadata"]["prediction_time_ms"]
        assert prediction_time < 5000  # 10 predictions should complete in under 5 seconds


# ===== Root Endpoint Tests =====


class TestRootEndpoint:
    """Tests for the landing page endpoint."""

    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_html(self, client):
        """Root endpoint should return HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_root_contains_key_elements(self, client):
        """Landing page should contain key information."""
        response = client.get("/")
        content = response.text

        # Check for main heading and branding
        assert "HR Attrition Prediction API" in content

        # Check for all endpoint links
        assert "/health" in content
        assert "/api/v1/model/info" in content
        assert "/api/v1/predict" in content
        assert "/api/v1/predict/batch" in content

        # Check for documentation links
        assert "/docs" in content
        assert "/redoc" in content

        # Check for GitHub link
        assert "github.com/ghislaindelabie/oc5-deploy-ml" in content

    def test_root_has_cache_headers(self, client):
        """Root endpoint should include caching headers."""
        response = client.get("/")
        assert "cache-control" in response.headers
        assert "max-age" in response.headers["cache-control"]

    def test_root_is_valid_html(self, client):
        """Landing page should be valid HTML."""
        response = client.get("/")
        content = response.text

        # Check for basic HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "</html>" in content

    def test_root_not_in_openapi_schema(self, client):
        """Root endpoint should not appear in OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        # The root path "/" should not be in the paths
        assert "/" not in openapi_spec.get("paths", {})
