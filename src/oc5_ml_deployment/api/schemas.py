"""
Pydantic schemas for API request/response validation.

These schemas define the contract between the API and its clients.
All validation rules are defined here and can be adjusted based on
data analysis and business requirements.
"""

from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmployeeFeatures(BaseModel):
    """
    Input features for a single employee prediction.

    NOTE: Validation ranges are initial estimates and should be reviewed
    against actual data distributions and business rules.
    """

    # Numeric features
    age: int = Field(..., ge=18, le=70, description="Employee age in years")
    revenu_mensuel: float = Field(..., gt=0, description="Monthly income in currency units")
    nombre_experiences_precedentes: int = Field(..., ge=0, le=50, description="Number of previous companies")
    nombre_heures_travailless: int = Field(..., ge=0, le=168, description="Standard working hours per week")
    annees_dans_le_poste_actuel: int = Field(..., ge=0, le=50, description="Years in current role")

    # Satisfaction scores (Likert scale 1-5)
    satisfaction_employee_environnement: int = Field(..., ge=1, le=5, description="Environment satisfaction")
    satisfaction_employee_nature_travail: int = Field(..., ge=1, le=5, description="Job nature satisfaction")
    satisfaction_employee_equipe: int = Field(..., ge=1, le=5, description="Team satisfaction")
    satisfaction_employee_equilibre_pro_perso: int = Field(..., ge=1, le=5, description="Work-life balance satisfaction")

    # Performance ratings (1-4 scale)
    note_evaluation_precedente: int = Field(..., ge=1, le=4, description="Previous performance rating")
    note_evaluation_actuelle: int = Field(..., ge=1, le=4, description="Current performance rating")

    # Other numeric features
    nombre_participation_pee: int = Field(..., ge=0, description="Number of employee savings plan participations")
    nb_formations_suivies: int = Field(..., ge=0, le=20, description="Number of training courses completed")
    nombre_employee_sous_responsabilite: int = Field(..., ge=0, description="Number of employees managed")
    distance_domicile_travail: int = Field(..., ge=0, description="Distance from home to work (km)")
    niveau_education: int = Field(..., ge=1, le=5, description="Education level (1-5)")
    annees_depuis_la_derniere_promotion: int = Field(..., ge=0, le=50, description="Years since last promotion")
    annes_sous_responsable_actuel: int = Field(..., ge=0, le=50, description="Years under current manager")

    # Categorical features
    genre: str = Field(..., description="Gender")
    statut_marital: str = Field(..., description="Marital status")
    departement: str = Field(..., description="Department")
    poste: str = Field(..., description="Job position")
    domaine_etude: str = Field(..., description="Field of study")
    heure_supplementaires: Literal["Yes", "No"] = Field(..., description="Works overtime")

    @field_validator('genre')
    @classmethod
    def validate_genre(cls, v: str) -> str:
        """Validate gender field."""
        allowed = {"Male", "Female", "M", "F", "Homme", "Femme"}
        if v not in allowed:
            raise ValueError(f"Genre must be one of {allowed}")
        return v

    @field_validator('statut_marital')
    @classmethod
    def validate_statut_marital(cls, v: str) -> str:
        """Validate marital status field."""
        allowed = {"Single", "Married", "Divorced", "Célibataire", "Marié", "Divorcé"}
        if v not in allowed:
            raise ValueError(f"Statut marital must be one of {allowed}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
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
        }
    }


class PredictionResult(BaseModel):
    """Single prediction result."""
    will_leave: bool = Field(..., description="Prediction: will the employee leave?")
    probability_leave: float = Field(..., ge=0, le=100, description="Probability of leaving (percentage)")
    probability_stay: float = Field(..., ge=0, le=100, description="Probability of staying (percentage)")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Risk categorization")


class PredictionResponse(BaseModel):
    """Response for single prediction endpoint."""
    prediction: PredictionResult
    metadata: dict = Field(..., description="Prediction metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "prediction": {
                    "will_leave": False,
                    "probability_leave": 23.4,
                    "probability_stay": 76.6,
                    "risk_level": "low"
                },
                "metadata": {
                    "model_version": "xgb_enhanced_v1.0",
                    "prediction_time_ms": 12,
                    "timestamp": "2025-11-14T10:30:00Z"
                }
            }
        }
    }


class EmployeeBatchItem(EmployeeFeatures):
    """Employee data with ID for batch predictions."""
    employee_id: str = Field(..., description="Unique employee identifier")


class BatchPredictionRequest(BaseModel):
    """Request for batch prediction endpoint."""
    employees: list[EmployeeBatchItem] = Field(..., min_length=1, max_length=100)

    model_config = {
        "json_schema_extra": {
            "example": {
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
                    }
                ]
            }
        }
    }


class BatchPredictionItem(BaseModel):
    """Single prediction result in batch response."""
    employee_id: str
    will_leave: bool
    probability_leave: float = Field(..., ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class BatchPredictionResponse(BaseModel):
    """Response for batch prediction endpoint."""
    predictions: list[BatchPredictionItem]
    metadata: dict

    model_config = {
        "json_schema_extra": {
            "example": {
                "predictions": [
                    {
                        "employee_id": "EMP001",
                        "will_leave": False,
                        "probability_leave": 23.4,
                        "risk_level": "low"
                    },
                    {
                        "employee_id": "EMP002",
                        "will_leave": True,
                        "probability_leave": 68.2,
                        "risk_level": "high"
                    }
                ],
                "metadata": {
                    "total_predictions": 2,
                    "model_version": "xgb_enhanced_v1.0",
                    "prediction_time_ms": 45,
                    "timestamp": "2025-11-14T10:30:00Z"
                }
            }
        }
    }


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: Literal["healthy", "unhealthy"]
    model_loaded: bool
    model_version: Optional[str] = None
    timestamp: str

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "model_version": "xgb_enhanced_v1.0",
                "timestamp": "2025-11-14T10:30:00Z"
            }
        }
    )


class ModelInfoResponse(BaseModel):
    """Response for model info endpoint."""
    model_version: str
    training_date: str
    performance_metrics: dict
    features_required: dict

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "model_version": "xgb_enhanced_v1.0",
                "training_date": "2025-11-13T23:27:36",
                "performance_metrics": {
                    "accuracy": 0.872,
                    "precision": 0.688,
                    "recall": 0.384,
                    "f1_score": 0.488,
                    "roc_auc": 0.834
                },
                "features_required": {
                    "numeric": ["age", "revenu_mensuel"],
                    "categorical": ["genre", "statut_marital"]
                }
            }
        }
    )
