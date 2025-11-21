"""
Shared pytest fixtures for all test modules.

This file provides common fixtures that can be used across all test files.
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from oc5_ml_deployment.api.main import app


@pytest.fixture
def client():
    """Create a FastAPI test client.

    This fixture provides a TestClient instance that can be used to make
    HTTP requests to the API during testing.

    Note: For database tests that require async operations, use async_client instead.
    """
    return TestClient(app)


@pytest.fixture
@pytest.mark.asyncio
async def async_client():
    """Create an async HTTP client for testing.

    This fixture provides an httpx.AsyncClient instance that can be used for
    async HTTP requests. Unlike TestClient, this works properly with async
    database operations.

    Usage:
        @pytest.mark.asyncio
        async def test_something(async_client):
            response = await async_client.post("/api/v1/predict", json=data)
            assert response.status_code == 200
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


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
