"""
Tests for API error handling and edge cases.

This module tests error responses, validation failures, and edge cases
to improve code coverage for error paths in main.py.
"""
import pytest
from fastapi.testclient import TestClient


def test_predict_with_invalid_data_type(client):
    """Test prediction endpoint with invalid data types."""
    response = client.post(
        "/api/v1/predict",
        json={
            "employee_id": "TEST_001",
            "age": "not_a_number",  # Invalid: should be int
            "genre": "Male",
            "statut_marital": "Married",
            "departement": "Sales",
            "poste": "Sales Executive",
            "domaine_etude": "Life Sciences",
            "revenu_mensuel": 5000,
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
            "heure_supplementaires": "No",
        }
    )

    assert response.status_code == 422


def test_predict_with_missing_required_field(client):
    """Test prediction endpoint with missing required field."""
    response = client.post(
        "/api/v1/predict",
        json={
            "employee_id": "TEST_001",
            # Missing "age" field
            "genre": "Male",
            "statut_marital": "Married",
            "departement": "Sales",
        }
    )

    assert response.status_code == 422


def test_predict_with_invalid_categorical_value(client):
    """Test prediction endpoint with invalid categorical value."""
    response = client.post(
        "/api/v1/predict",
        json={
            "employee_id": "TEST_001",
            "age": 35,
            "genre": "InvalidGender",  # Invalid value
            "statut_marital": "Married",
            "departement": "Sales",
            "poste": "Sales Executive",
            "domaine_etude": "Life Sciences",
            "revenu_mensuel": 5000,
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
            "heure_supplementaires": "No",
        }
    )

    assert response.status_code == 422


def test_batch_predict_with_empty_list(client):
    """Test batch prediction with empty employee list."""
    response = client.post(
        "/api/v1/predict/batch",
        json={"employees": []}
    )

    assert response.status_code == 422


def test_batch_predict_exceeding_max_limit(client):
    """Test batch prediction exceeding 100 employee limit."""
    # Create 101 employees (exceeds limit)
    employees = []
    for i in range(101):
        employees.append({
            "employee_id": f"TEST_{i:03d}",
            "age": 35,
            "genre": "Male",
            "statut_marital": "Married",
            "departement": "Sales",
            "poste": "Sales Executive",
            "domaine_etude": "Life Sciences",
            "revenu_mensuel": 5000,
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
            "heure_supplementaires": "No",
        })

    response = client.post(
        "/api/v1/predict/batch",
        json={"employees": employees}
    )

    assert response.status_code == 422


def test_landing_page_returns_html(client):
    """Test that landing page returns HTML content."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Check for some expected content
    assert "HR Attrition Prediction API" in response.text or "API" in response.text
