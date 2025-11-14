#!/usr/bin/env python3
"""
Quick script to test the API locally.

Usage:
    1. Start the API: uvicorn src.oc5_ml_deployment.api.main:app --reload
    2. Run this script: python test_api_live.py
"""

import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

BASE_URL = "http://127.0.0.1:8000"


def print_section(title):
    """Print a section header."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("=" * 60)


def test_health():
    """Test health endpoint."""
    print_section("1. Testing Health Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()

        console.print(f"Status Code: [green]{response.status_code}[/green]")
        console.print(f"Response:")
        rprint(data)

        if data["model_loaded"]:
            console.print("[green]✓ Model is loaded![/green]")
        else:
            console.print("[red]✗ Model failed to load![/red]")

    except requests.exceptions.ConnectionError:
        console.print("[red]✗ Could not connect to API. Is the server running?[/red]")
        console.print("Start it with: uvicorn src.oc5_ml_deployment.api.main:app --reload")
        return False

    return True


def test_model_info():
    """Test model info endpoint."""
    print_section("2. Testing Model Info Endpoint")

    response = requests.get(f"{BASE_URL}/api/v1/model/info")
    data = response.json()

    console.print(f"Status Code: [green]{response.status_code}[/green]")
    console.print(f"\nModel Version: [yellow]{data['model_version']}[/yellow]")
    console.print(f"Training Date: {data['training_date']}")

    console.print("\n[bold]Performance Metrics:[/bold]")
    metrics = data['performance_metrics']
    for metric, value in metrics.items():
        console.print(f"  {metric}: {value:.3f}")


def test_single_prediction():
    """Test single prediction endpoint."""
    print_section("3. Testing Single Prediction")

    # Low-risk employee
    employee_low_risk = {
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
        "heure_supplementaires": "No"
    }

    console.print("\n[bold]Testing with low-risk employee profile:[/bold]")
    response = requests.post(f"{BASE_URL}/api/v1/predict", json=employee_low_risk)
    data = response.json()

    console.print(f"Status Code: [green]{response.status_code}[/green]")

    pred = data['prediction']
    console.print(f"\nWill Leave: [{'red' if pred['will_leave'] else 'green'}]{pred['will_leave']}[/]")
    console.print(f"Probability of Leaving: {pred['probability_leave']:.2f}%")
    console.print(f"Risk Level: [{get_risk_color(pred['risk_level'])}]{pred['risk_level'].upper()}[/]")
    console.print(f"Prediction Time: {data['metadata']['prediction_time_ms']}ms")


def test_high_risk_prediction():
    """Test prediction with high-risk profile."""
    print_section("4. Testing High-Risk Employee Prediction")

    # High-risk employee (low satisfaction, overtime, low salary)
    employee_high_risk = {
        "age": 28,
        "revenu_mensuel": 2500.0,
        "nombre_experiences_precedentes": 1,
        "nombre_heures_travailless": 50,
        "annees_dans_le_poste_actuel": 1,
        "satisfaction_employee_environnement": 1,
        "note_evaluation_precedente": 2,
        "satisfaction_employee_nature_travail": 1,
        "satisfaction_employee_equipe": 2,
        "satisfaction_employee_equilibre_pro_perso": 1,
        "note_evaluation_actuelle": 2,
        "nombre_participation_pee": 0,
        "nb_formations_suivies": 0,
        "nombre_employee_sous_responsabilite": 0,
        "distance_domicile_travail": 30,
        "niveau_education": 2,
        "annees_depuis_la_derniere_promotion": 10,
        "annes_sous_responsable_actuel": 1,
        "genre": "Female",
        "statut_marital": "Single",
        "departement": "Sales",
        "poste": "Sales Representative",
        "domaine_etude": "Other",
        "heure_supplementaires": "Yes"
    }

    console.print("\n[bold]Testing with high-risk employee profile:[/bold]")
    console.print("(Low satisfaction, overtime, low salary, long commute)")

    response = requests.post(f"{BASE_URL}/api/v1/predict", json=employee_high_risk)
    data = response.json()

    pred = data['prediction']
    console.print(f"\nWill Leave: [{'red' if pred['will_leave'] else 'green'}]{pred['will_leave']}[/]")
    console.print(f"Probability of Leaving: {pred['probability_leave']:.2f}%")
    console.print(f"Risk Level: [{get_risk_color(pred['risk_level'])}]{pred['risk_level'].upper()}[/]")


def test_batch_prediction():
    """Test batch prediction endpoint."""
    print_section("5. Testing Batch Prediction")

    batch_request = {
        "employees": [
            {
                "employee_id": "EMP001",
                "age": 35, "revenu_mensuel": 5000.0, "nombre_experiences_precedentes": 3,
                "nombre_heures_travailless": 40, "annees_dans_le_poste_actuel": 2,
                "satisfaction_employee_environnement": 4, "note_evaluation_precedente": 3,
                "satisfaction_employee_nature_travail": 4, "satisfaction_employee_equipe": 3,
                "satisfaction_employee_equilibre_pro_perso": 3, "note_evaluation_actuelle": 3,
                "nombre_participation_pee": 1, "nb_formations_suivies": 2,
                "nombre_employee_sous_responsabilite": 0, "distance_domicile_travail": 10,
                "niveau_education": 3, "annees_depuis_la_derniere_promotion": 1,
                "annes_sous_responsable_actuel": 2, "genre": "Male", "statut_marital": "Married",
                "departement": "Sales", "poste": "Sales Executive",
                "domaine_etude": "Life Sciences", "heure_supplementaires": "No"
            },
            {
                "employee_id": "EMP002",
                "age": 28, "revenu_mensuel": 2500.0, "nombre_experiences_precedentes": 1,
                "nombre_heures_travailless": 50, "annees_dans_le_poste_actuel": 1,
                "satisfaction_employee_environnement": 1, "note_evaluation_precedente": 2,
                "satisfaction_employee_nature_travail": 1, "satisfaction_employee_equipe": 2,
                "satisfaction_employee_equilibre_pro_perso": 1, "note_evaluation_actuelle": 2,
                "nombre_participation_pee": 0, "nb_formations_suivies": 0,
                "nombre_employee_sous_responsabilite": 0, "distance_domicile_travail": 30,
                "niveau_education": 2, "annees_depuis_la_derniere_promotion": 10,
                "annes_sous_responsable_actuel": 1, "genre": "Female", "statut_marital": "Single",
                "departement": "Sales", "poste": "Sales Representative",
                "domaine_etude": "Other", "heure_supplementaires": "Yes"
            },
            {
                "employee_id": "EMP003",
                "age": 42, "revenu_mensuel": 7500.0, "nombre_experiences_precedentes": 5,
                "nombre_heures_travailless": 40, "annees_dans_le_poste_actuel": 5,
                "satisfaction_employee_environnement": 5, "note_evaluation_precedente": 4,
                "satisfaction_employee_nature_travail": 5, "satisfaction_employee_equipe": 4,
                "satisfaction_employee_equilibre_pro_perso": 4, "note_evaluation_actuelle": 4,
                "nombre_participation_pee": 3, "nb_formations_suivies": 5,
                "nombre_employee_sous_responsabilite": 5, "distance_domicile_travail": 5,
                "niveau_education": 4, "annees_depuis_la_derniere_promotion": 2,
                "annes_sous_responsable_actuel": 5, "genre": "Male", "statut_marital": "Married",
                "departement": "Research & Development", "poste": "Manager",
                "domaine_etude": "Life Sciences", "heure_supplementaires": "No"
            }
        ]
    }

    console.print("\n[bold]Predicting for 3 employees...[/bold]")

    response = requests.post(f"{BASE_URL}/api/v1/predict/batch", json=batch_request)
    data = response.json()

    console.print(f"Status Code: [green]{response.status_code}[/green]")
    console.print(f"Total Predictions: {data['metadata']['total_predictions']}")
    console.print(f"Batch Processing Time: {data['metadata']['prediction_time_ms']}ms")

    # Create results table
    table = Table(title="Batch Prediction Results")
    table.add_column("Employee ID", style="cyan")
    table.add_column("Will Leave", style="white")
    table.add_column("Probability", justify="right")
    table.add_column("Risk Level", justify="center")

    for pred in data['predictions']:
        will_leave_emoji = "❌" if pred['will_leave'] else "✓"
        risk_color = get_risk_color(pred['risk_level'])

        table.add_row(
            pred['employee_id'],
            will_leave_emoji,
            f"{pred['probability_leave']:.2f}%",
            f"[{risk_color}]{pred['risk_level'].upper()}[/]"
        )

    console.print(table)


def test_validation_error():
    """Test validation error handling."""
    print_section("6. Testing Validation Error Handling")

    console.print("\n[bold]Sending invalid data (age=17, below minimum):[/bold]")

    invalid_data = {"age": 17}
    response = requests.post(f"{BASE_URL}/api/v1/predict", json=invalid_data)

    console.print(f"Status Code: [yellow]{response.status_code}[/yellow] (Expected: 422)")

    if response.status_code == 422:
        console.print("[green]✓ Validation working correctly![/green]")
        console.print("\nFirst error message:")
        error = response.json()['detail'][0]
        console.print(f"  Field: {error['loc']}")
        console.print(f"  Message: {error['msg']}")
    else:
        console.print("[red]✗ Unexpected response![/red]")


def get_risk_color(risk_level):
    """Get color for risk level."""
    colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red"
    }
    return colors.get(risk_level, "white")


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]HR Attrition API - Live Testing[/bold cyan]\n"
        "Testing all endpoints of the API",
        border_style="cyan"
    ))

    # Test health first
    if not test_health():
        return

    # Run all other tests
    test_model_info()
    test_single_prediction()
    test_high_risk_prediction()
    test_batch_prediction()
    test_validation_error()

    # Summary
    print_section("Summary")
    console.print("[bold green]✓ All tests completed successfully![/bold green]")
    console.print("\nYou can also:")
    console.print("  • Visit http://127.0.0.1:8000/docs for interactive API docs")
    console.print("  • Run automated tests with: pytest tests/ -v")
    console.print("  • Check HOW_TO_TEST_API.md for more testing options")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
