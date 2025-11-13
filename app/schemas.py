"""
Pydantic Schemas for API Request/Response Validation

This module defines all data models for the HR Attrition API.

Schemas to implement:
    1. EmployeeInput - 26 features with validation rules
    2. PredictionOutput - prediction result with risk assessment
    3. PredictionListResponse - for batch predictions (optional)
    4. HealthResponse - API health check response
    5. ErrorResponse - standardized error format

EmployeeInput Features (26 total):

    Numeric (22):
        - age: int (18-70)
        - revenu_mensuel: int (>0)
        - nombre_heures_travailless: int (0-168)
        - nombre_experiences_precedentes: int (>=0)
        - annees_dans_le_poste_actuel: int (>=0)
        - satisfaction_employee_environnement: int (1-4)
        - satisfaction_employee_nature_travail: int (1-4)
        - satisfaction_employee_equipe: int (1-4)
        - satisfaction_employee_equilibre_pro_perso: int (1-4)
        - note_evaluation_precedente: int (1-4)
        - note_evaluation_actuelle: int (1-4)
        - nombre_participation_pee: int (>=0)
        - nb_formations_suivies: int (>=0)
        - distance_domicile_travail: int (>=0)
        - frequence_deplacement: int (1-4)
        - annees_depuis_la_derniere_promotion: int (>=0)
        - annes_sous_responsable_actuel: int (>=0)

    Categorical (6):
        - genre: str (M|F)
        - statut_marital: str (Célibataire|Marié(e)|Divorcé(e))
        - departement: str (Commercial|Consulting|RH|etc.)
        - poste: str (free text)
        - domaine_etude: str (Infra & Cloud|Autre|etc.)
        - heure_supplementaires: str (Oui|Non)

PredictionOutput Fields:
    - prediction: str ("Oui" or "Non")
    - probability: float (0-1)
    - risk_level: str ("High"|"Medium"|"Low")
    - top_risk_factors: List[str] (top 3 contributing features)
    - model_version: str ("xgb_enhanced_v1")
    - prediction_id: Optional[int] (DB record ID if saved)

Risk Level Logic:
    - High: probability >= 0.6
    - Medium: 0.4 <= probability < 0.6
    - Low: probability < 0.4

TODO:
    - from pydantic import BaseModel, Field, validator
    - Define each schema class
    - Add field descriptions
    - Add example data in Config.schema_extra
    - Add custom validators if needed (e.g., enum validation)
"""

# CODE TO BE WRITTEN IN PHASE 1
