"""
Shared pytest fixtures for all test modules.

This file provides common fixtures that can be used across all test files.
"""
import pytest
from fastapi.testclient import TestClient
from oc5_ml_deployment.api.main import app


@pytest.fixture
def client():
    """Create a FastAPI test client.

    This fixture provides a TestClient instance that can be used to make
    HTTP requests to the API during testing.
    """
    return TestClient(app)


@pytest.fixture
def valid_employee_data():
    """Valid employee data for testing predictions.

    Returns a dictionary with all required employee features for making
    a prediction request.
    """
    return {
        "employee_id": "TEST_001",
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
    }
