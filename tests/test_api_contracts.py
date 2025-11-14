"""
Contract Tests for API Schemas

These tests verify that Pydantic schemas correctly validate input/output data
according to the API contract. They should be run BEFORE implementing endpoints.

Test coverage:
- Valid inputs are accepted
- Invalid inputs are rejected with appropriate errors
- Field validation rules work correctly
- Response schemas match expected format
"""

import pytest
from pydantic import ValidationError
from src.oc5_ml_deployment.api.schemas import (
    EmployeeFeatures,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
)


# Test fixtures
@pytest.fixture
def valid_employee_data():
    """Valid employee data for testing."""
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


# ===== EmployeeFeatures Schema Tests =====


class TestEmployeeFeaturesValidation:
    """Test validation rules for EmployeeFeatures schema."""

    def test_valid_employee_data_is_accepted(self, valid_employee_data):
        """Valid employee data should pass validation."""
        employee = EmployeeFeatures(**valid_employee_data)
        assert employee.age == 35
        assert employee.revenu_mensuel == 5000.0
        assert employee.genre == "Male"

    def test_missing_required_field_raises_error(self, valid_employee_data):
        """Missing required fields should raise ValidationError."""
        invalid_data = valid_employee_data.copy()
        del invalid_data["age"]

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("age",) and e["type"] == "missing" for e in errors)

    def test_age_below_minimum_raises_error(self, valid_employee_data):
        """Age below 18 should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["age"] = 17

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("age",) for e in errors)

    def test_age_above_maximum_raises_error(self, valid_employee_data):
        """Age above 70 should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["age"] = 71

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("age",) for e in errors)

    def test_age_at_boundaries_is_accepted(self, valid_employee_data):
        """Age at exact boundaries (18, 70) should be accepted."""
        # Test minimum
        data_min = valid_employee_data.copy()
        data_min["age"] = 18
        employee_min = EmployeeFeatures(**data_min)
        assert employee_min.age == 18

        # Test maximum
        data_max = valid_employee_data.copy()
        data_max["age"] = 70
        employee_max = EmployeeFeatures(**data_max)
        assert employee_max.age == 70

    def test_negative_revenu_raises_error(self, valid_employee_data):
        """Negative or zero revenue should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["revenu_mensuel"] = -100

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("revenu_mensuel",) for e in errors)

    def test_zero_revenu_raises_error(self, valid_employee_data):
        """Zero revenue should be rejected (gt=0, not ge=0)."""
        invalid_data = valid_employee_data.copy()
        invalid_data["revenu_mensuel"] = 0

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("revenu_mensuel",) for e in errors)

    def test_satisfaction_scores_out_of_range_raises_error(self, valid_employee_data):
        """Satisfaction scores outside 1-5 range should be rejected."""
        # Test below minimum
        invalid_data = valid_employee_data.copy()
        invalid_data["satisfaction_employee_environnement"] = 0

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

        # Test above maximum
        invalid_data["satisfaction_employee_environnement"] = 6

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

    def test_note_evaluation_out_of_range_raises_error(self, valid_employee_data):
        """Performance ratings outside 1-4 range should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["note_evaluation_actuelle"] = 5

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

    def test_invalid_genre_raises_error(self, valid_employee_data):
        """Invalid gender values should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["genre"] = "Unknown"

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("genre",) for e in errors)

    def test_valid_genre_variants_are_accepted(self, valid_employee_data):
        """Different valid gender formats should be accepted."""
        valid_genres = ["Male", "Female", "M", "F", "Homme", "Femme"]

        for genre in valid_genres:
            data = valid_employee_data.copy()
            data["genre"] = genre
            employee = EmployeeFeatures(**data)
            assert employee.genre == genre

    def test_invalid_statut_marital_raises_error(self, valid_employee_data):
        """Invalid marital status should be rejected."""
        invalid_data = valid_employee_data.copy()
        invalid_data["statut_marital"] = "Complicated"

        with pytest.raises(ValidationError) as exc_info:
            EmployeeFeatures(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("statut_marital",) for e in errors)

    def test_valid_statut_marital_variants_are_accepted(self, valid_employee_data):
        """Different valid marital status formats should be accepted."""
        valid_statuses = ["Single", "Married", "Divorced", "Célibataire", "Marié", "Divorcé"]

        for status in valid_statuses:
            data = valid_employee_data.copy()
            data["statut_marital"] = status
            employee = EmployeeFeatures(**data)
            assert employee.statut_marital == status

    def test_heure_supplementaires_only_accepts_yes_no(self, valid_employee_data):
        """Overtime field should only accept 'Yes' or 'No'."""
        # Valid values
        for value in ["Yes", "No"]:
            data = valid_employee_data.copy()
            data["heure_supplementaires"] = value
            employee = EmployeeFeatures(**data)
            assert employee.heure_supplementaires == value

        # Invalid value
        invalid_data = valid_employee_data.copy()
        invalid_data["heure_supplementaires"] = "Maybe"

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

    def test_wrong_field_types_raise_error(self, valid_employee_data):
        """Fields with wrong types should be rejected."""
        # String instead of int
        invalid_data = valid_employee_data.copy()
        invalid_data["age"] = "thirty-five"

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

        # Int instead of string
        invalid_data = valid_employee_data.copy()
        invalid_data["genre"] = 123

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)

    def test_negative_values_for_count_fields_raise_error(self, valid_employee_data):
        """Count fields should not accept negative values."""
        invalid_data = valid_employee_data.copy()
        invalid_data["nombre_experiences_precedentes"] = -1

        with pytest.raises(ValidationError):
            EmployeeFeatures(**invalid_data)


# ===== BatchPredictionRequest Schema Tests =====


class TestBatchPredictionRequest:
    """Test batch prediction request validation."""

    def test_valid_batch_request_is_accepted(self, valid_employee_data):
        """Valid batch request with employee IDs should pass."""
        batch_data = {
            "employees": [
                {"employee_id": "EMP001", **valid_employee_data},
                {"employee_id": "EMP002", **valid_employee_data},
            ]
        }

        batch_request = BatchPredictionRequest(**batch_data)
        assert len(batch_request.employees) == 2
        assert batch_request.employees[0].employee_id == "EMP001"

    def test_empty_employees_list_raises_error(self):
        """Empty employees list should be rejected."""
        batch_data = {"employees": []}

        with pytest.raises(ValidationError) as exc_info:
            BatchPredictionRequest(**batch_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("employees",) for e in errors)

    def test_batch_size_limit_enforced(self, valid_employee_data):
        """Batch requests exceeding max size (100) should be rejected."""
        batch_data = {
            "employees": [
                {"employee_id": f"EMP{i:03d}", **valid_employee_data}
                for i in range(101)
            ]
        }

        with pytest.raises(ValidationError) as exc_info:
            BatchPredictionRequest(**batch_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("employees",) for e in errors)

    def test_missing_employee_id_raises_error(self, valid_employee_data):
        """Batch items missing employee_id should be rejected."""
        batch_data = {"employees": [valid_employee_data]}  # Missing employee_id

        with pytest.raises(ValidationError) as exc_info:
            BatchPredictionRequest(**batch_data)

        errors = exc_info.value.errors()
        assert any("employee_id" in str(e["loc"]) for e in errors)


# ===== Response Schema Tests =====


class TestPredictionResponse:
    """Test prediction response schema."""

    def test_valid_prediction_response_is_accepted(self):
        """Valid prediction response should pass validation."""
        response_data = {
            "prediction": {
                "will_leave": False,
                "probability_leave": 23.4,
                "probability_stay": 76.6,
                "risk_level": "low",
            },
            "metadata": {
                "model_version": "xgb_enhanced_v1.0",
                "prediction_time_ms": 12,
                "timestamp": "2025-11-14T10:30:00Z",
            },
        }

        response = PredictionResponse(**response_data)
        assert response.prediction.will_leave is False
        assert response.prediction.probability_leave == 23.4
        assert response.prediction.risk_level == "low"

    def test_probability_outside_range_raises_error(self):
        """Probabilities outside 0-100 range should be rejected."""
        response_data = {
            "prediction": {
                "will_leave": False,
                "probability_leave": 150.0,  # Invalid
                "probability_stay": 76.6,
                "risk_level": "low",
            },
            "metadata": {"model_version": "v1", "prediction_time_ms": 12, "timestamp": "2025-11-14T10:30:00Z"},
        }

        with pytest.raises(ValidationError):
            PredictionResponse(**response_data)

    def test_invalid_risk_level_raises_error(self):
        """Risk levels other than low/medium/high should be rejected."""
        response_data = {
            "prediction": {
                "will_leave": False,
                "probability_leave": 23.4,
                "probability_stay": 76.6,
                "risk_level": "critical",  # Invalid
            },
            "metadata": {"model_version": "v1", "prediction_time_ms": 12, "timestamp": "2025-11-14T10:30:00Z"},
        }

        with pytest.raises(ValidationError):
            PredictionResponse(**response_data)


class TestHealthResponse:
    """Test health check response schema."""

    def test_valid_health_response_is_accepted(self):
        """Valid health response should pass validation."""
        health_data = {
            "status": "healthy",
            "model_loaded": True,
            "model_version": "xgb_enhanced_v1.0",
            "timestamp": "2025-11-14T10:30:00Z",
        }

        response = HealthResponse(**health_data)
        assert response.status == "healthy"
        assert response.model_loaded is True

    def test_invalid_status_raises_error(self):
        """Status other than healthy/unhealthy should be rejected."""
        health_data = {
            "status": "ok",  # Invalid
            "model_loaded": True,
            "timestamp": "2025-11-14T10:30:00Z",
        }

        with pytest.raises(ValidationError):
            HealthResponse(**health_data)


# ===== Edge Cases =====


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_minimum_values_are_accepted(self, valid_employee_data):
        """Test with all fields at their minimum allowed values."""
        edge_data = valid_employee_data.copy()
        edge_data.update(
            {
                "age": 18,
                "revenu_mensuel": 0.01,
                "nombre_experiences_precedentes": 0,
                "nombre_heures_travailless": 0,
                "annees_dans_le_poste_actuel": 0,
                "satisfaction_employee_environnement": 1,
                "note_evaluation_precedente": 1,
                "satisfaction_employee_nature_travail": 1,
                "satisfaction_employee_equipe": 1,
                "satisfaction_employee_equilibre_pro_perso": 1,
                "note_evaluation_actuelle": 1,
                "nombre_participation_pee": 0,
                "nb_formations_suivies": 0,
                "nombre_employee_sous_responsabilite": 0,
                "distance_domicile_travail": 0,
                "niveau_education": 1,
                "annees_depuis_la_derniere_promotion": 0,
                "annes_sous_responsable_actuel": 0,
            }
        )

        employee = EmployeeFeatures(**edge_data)
        assert employee.age == 18
        assert employee.satisfaction_employee_environnement == 1

    def test_all_maximum_values_are_accepted(self, valid_employee_data):
        """Test with all fields at their maximum allowed values."""
        edge_data = valid_employee_data.copy()
        edge_data.update(
            {
                "age": 70,
                "nombre_experiences_precedentes": 50,
                "nombre_heures_travailless": 168,
                "annees_dans_le_poste_actuel": 50,
                "satisfaction_employee_environnement": 5,
                "note_evaluation_precedente": 4,
                "satisfaction_employee_nature_travail": 5,
                "satisfaction_employee_equipe": 5,
                "satisfaction_employee_equilibre_pro_perso": 5,
                "note_evaluation_actuelle": 4,
                "nb_formations_suivies": 20,
                "niveau_education": 5,
                "annees_depuis_la_derniere_promotion": 50,
                "annes_sous_responsable_actuel": 50,
            }
        )

        employee = EmployeeFeatures(**edge_data)
        assert employee.age == 70
        assert employee.satisfaction_employee_environnement == 5

    def test_special_characters_in_text_fields(self, valid_employee_data):
        """Test that text fields handle accents and special characters."""
        special_data = valid_employee_data.copy()
        special_data.update(
            {
                "poste": "Développeur Sénior",
                "departement": "Recherche & Développement",
                "domaine_etude": "Sciences de l'ingénieur",
            }
        )

        employee = EmployeeFeatures(**special_data)
        assert "é" in employee.poste
        assert "&" in employee.departement
        assert "'" in employee.domaine_etude
