# How to Test the API Locally

## Method 1: Interactive Swagger UI (Recommended)

### Start the Server

```bash
uvicorn src.oc5_ml_deployment.api.main:app --reload
```

### Access Interactive Documentation

Open in your browser:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Testing with Swagger UI

1. **Click on any endpoint** (e.g., `GET /health`)
2. **Click "Try it out"**
3. **Click "Execute"**
4. **See the response** below

For prediction endpoints:
1. Click on `POST /api/v1/predict`
2. Click "Try it out"
3. Edit the JSON request body (pre-filled example)
4. Click "Execute"
5. View the prediction result!

---

## Method 2: Using curl Commands

### Health Check
```bash
curl http://127.0.0.1:8000/health | python -m json.tool
```

Expected output:
```json
{
    "status": "healthy",
    "model_loaded": true,
    "model_version": "xgb_enhanced_v1.0",
    "timestamp": "2025-11-14T10:30:00Z"
}
```

### Model Info
```bash
curl http://127.0.0.1:8000/api/v1/model/info | python -m json.tool
```

### Single Prediction

Create a test file `test_employee.json`:
```json
{
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
```

Then run:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_employee.json | python -m json.tool
```

Expected output:
```json
{
    "prediction": {
        "will_leave": false,
        "probability_leave": 7.5,
        "probability_stay": 92.5,
        "risk_level": "low"
    },
    "metadata": {
        "model_version": "xgb_enhanced_v1.0",
        "prediction_time_ms": 25,
        "timestamp": "2025-11-14T10:30:00Z"
    }
}
```

### Batch Prediction

Create `test_batch.json`:
```json
{
  "employees": [
    {
      "employee_id": "EMP001",
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
    },
    {
      "employee_id": "EMP002",
      "age": 28,
      "revenu_mensuel": 3000.0,
      "nombre_experiences_precedentes": 1,
      "nombre_heures_travailless": 50,
      "annees_dans_le_poste_actuel": 1,
      "satisfaction_employee_environnement": 2,
      "note_evaluation_precedente": 3,
      "satisfaction_employee_nature_travail": 2,
      "satisfaction_employee_equipe": 2,
      "satisfaction_employee_equilibre_pro_perso": 1,
      "note_evaluation_actuelle": 3,
      "nombre_participation_pee": 0,
      "nb_formations_suivies": 0,
      "nombre_employee_sous_responsabilite": 0,
      "distance_domicile_travail": 25,
      "niveau_education": 2,
      "annees_depuis_la_derniere_promotion": 5,
      "annes_sous_responsable_actuel": 1,
      "genre": "Female",
      "statut_marital": "Single",
      "departement": "Research & Development",
      "poste": "Laboratory Technician",
      "domaine_etude": "Life Sciences",
      "heure_supplementaires": "Yes"
    }
  ]
}
```

Then run:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d @test_batch.json | python -m json.tool
```

### SHAP Explanation

Get SHAP values explaining which features most influenced a prediction:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/explain \
  -H "Content-Type: application/json" \
  -d @test_employee.json | python -m json.tool
```

Expected output:
```json
{
    "top_features": [
        {
            "feature": "heure_supplementaires_Yes",
            "shap_value": 0.1523,
            "impact": "increases risk"
        },
        {
            "feature": "nombre_heures_travailless",
            "shap_value": 0.0892,
            "impact": "increases risk"
        },
        {
            "feature": "satisfaction_employee_environnement",
            "shap_value": -0.0654,
            "impact": "decreases risk"
        },
        {
            "feature": "revenu_mensuel",
            "shap_value": -0.0432,
            "impact": "decreases risk"
        },
        {
            "feature": "age",
            "shap_value": 0.0321,
            "impact": "increases risk"
        }
    ],
    "metadata": {
        "model_version": "xgb_enhanced_v1.0",
        "explanation_time_ms": 45,
        "timestamp": "2025-11-21T10:30:00Z"
    }
}
```

---

## Method 3: Using Python Requests

```python
import requests
import json

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Single prediction
employee_data = {
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

response = requests.post(
    f"{BASE_URL}/api/v1/predict",
    json=employee_data
)
print(json.dumps(response.json(), indent=2))

# SHAP explanation
response = requests.post(
    f"{BASE_URL}/api/v1/explain",
    json=employee_data
)
print(json.dumps(response.json(), indent=2))
```

---

## Method 4: Running Automated Tests

Run all tests:
```bash
pytest tests/ -v
```

Run only integration tests:
```bash
pytest tests/test_api_integration.py -v
```

Run only contract tests:
```bash
pytest tests/test_api_contracts.py -v
```

Run specific test:
```bash
pytest tests/test_api_integration.py::TestPredictEndpoint::test_predict_valid_input_returns_200 -v
```

---

## Testing Different Scenarios

### Test High-Risk Employee
Modify employee data to trigger high-risk prediction:
```json
{
  "age": 25,
  "revenu_mensuel": 2500.0,
  "satisfaction_employee_environnement": 1,
  "satisfaction_employee_nature_travail": 1,
  "satisfaction_employee_equipe": 1,
  "satisfaction_employee_equilibre_pro_perso": 1,
  "heure_supplementaires": "Yes",
  ...
}
```

### Test Validation Errors

Invalid age (should return 422):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 17}'
```

Missing required fields (should return 422):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 35}'
```

---

## Troubleshooting

### Port Already in Use
If you get "Address already in use" error:
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn src.oc5_ml_deployment.api.main:app --reload --port 8001
```

### Model Not Loading
Check that model files exist:
```bash
ls -lh model/
# Should show: hr_attrition_xgb_enhanced.joblib and feature_metadata.json
```

### Import Errors
Make sure you're in the project root and the package is installed:
```bash
pip install -e .
```

---

## Quick Test Checklist

- [ ] Health endpoint returns "healthy"
- [ ] Model info shows correct version
- [ ] Single prediction returns valid result
- [ ] Batch prediction handles multiple employees
- [ ] SHAP explanation returns top 5 features with impacts
- [ ] Invalid input returns 422 error
- [ ] Swagger UI loads and works
- [ ] All automated tests pass
