# PRÉSENTATION POWERPOINT - Déploiement ML
## 10-12 slides pour soutenance

---

## SLIDE 1 - Page de titre

```
DÉPLOIEMENT D'UN MODÈLE DE MACHINE LEARNING
Prédiction de l'attrition des employés RH

OpenClassrooms - Projet 5
[Votre nom]
[Date]
```

---

## SLIDE 2 - Contexte et objectifs

**Titre**: Contexte et Objectifs du Projet

**Problématique**
- Prédire le risque de départ des employés
- Aider les RH à identifier les profils à risque
- Fournir des explications interprétables pour les prédictions

**Objectifs techniques**
- ✅ Entraîner un modèle XGBoost performant (ROC AUC ~0.85)
- ✅ Déployer une API REST production-ready
- ✅ Assurer la traçabilité avec une base de données
- ✅ Fournir l'interprétabilité via SHAP

**Livrable final**
API publique déployée sur Hugging Face Spaces avec CI/CD

---

## SLIDE 3 - Architecture globale

**Titre**: Architecture Globale du Système

```
┌──────────────────────────────────────────────────────────────┐
│                         UTILISATEURS                         │
│                    (Managers RH, API clients)                │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    HUGGING FACE SPACES                       │
│                    (Docker Container)                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              API FASTAPI (Port 7860)                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │  Endpoints   │  │ Model Service│  │   Schemas   │  │  │
│  │  │  /predict    │──│  XGBoost     │  │  Pydantic   │  │  │
│  │  │  /explain    │  │  + SHAP      │  │  Validation │  │  │
│  │  │  /batch      │  └──────────────┘  └─────────────┘  │  │
│  │  └──────────────┘                                      │  │
│  └─────────────────────┬──────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │ Async SQL
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                       │
│         (Logs de prédictions + métadonnées)                  │
└──────────────────────────────────────────────────────────────┘
```

**Composants principaux**:
- **FastAPI**: Framework web moderne et performant
- **XGBoost**: Modèle de classification pré-entraîné
- **SHAP**: Explications des prédictions
- **PostgreSQL**: Traçabilité et audit
- **Docker**: Conteneurisation pour déploiement

---

## SLIDE 4 - Pipeline Machine Learning

**Titre**: Pipeline d'Entraînement du Modèle

```
DONNÉES BRUTES (HR_comma_sep.csv)
         │
         │ 1. Chargement
         ▼
┌────────────────────────────────┐
│   Exploration & Nettoyage      │
│   - 26 features (num + cat)    │
│   - Target: attrition (0/1)    │
└────────┬───────────────────────┘
         │ 2. Prétraitement
         ▼
┌────────────────────────────────┐
│  Feature Engineering           │
│  - Encodage one-hot            │
│  - Standardisation             │
│  - Pipeline sklearn            │
└────────┬───────────────────────┘
         │ 3. Entraînement
         ▼
┌────────────────────────────────┐
│  XGBoost Enhanced              │
│  - Cross-validation 5-fold     │
│  - Optimisation hyperparamètres│
│  - Gestion déséquilibre classes│
└────────┬───────────────────────┘
         │ 4. Sauvegarde
         ▼
┌────────────────────────────────┐
│  Artifacts (354 KB)            │
│  - model.joblib                │
│  - feature_metadata.json       │
└────────────────────────────────┘
```

**Performances obtenues** (Cross-validation):
- Accuracy: 85.6%
- Precision: 62.5% @ 50% recall
- ROC AUC: 0.85
- F1-Score: 0.64

---

## SLIDE 5 - Architecture API (détails techniques)

**Titre**: Architecture de l'API FastAPI

```
CLIENT REQUEST
      │
      ▼
┌─────────────────────────────────────────┐
│         FASTAPI APPLICATION             │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │     ENDPOINTS LAYER               │  │
│  │  GET  /health                     │  │
│  │  GET  /api/v1/model/info          │  │
│  │  POST /api/v1/predict             │  │
│  │  POST /api/v1/predict/batch       │  │
│  │  POST /api/v1/explain             │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │   VALIDATION LAYER (Pydantic)    │  │
│  │  - EmployeeFeatures (26 champs)  │  │
│  │  - Validation types + ranges     │  │
│  │  - Schemas de réponse            │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │      BUSINESS LOGIC              │  │
│  │  ModelService                    │  │
│  │   ├─ load()                      │  │
│  │   ├─ predict()                   │  │
│  │   ├─ predict_batch()             │  │
│  │   └─ explain()  [SHAP]           │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │    DATABASE LAYER (optionnel)    │  │
│  │  - Log des prédictions           │  │
│  │  - Graceful degradation          │  │
│  │  - Rétention 365 jours           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Principes de design**:
- **Separation of concerns**: Couches distinctes
- **Dependency injection**: Services singleton
- **Graceful degradation**: L'API fonctionne sans BDD
- **Type safety**: Validation via Pydantic

---

## SLIDE 6 - Choix d'implémentation

**Titre**: Choix Techniques et Justifications

| **Aspect** | **Choix** | **Justification** |
|------------|-----------|-------------------|
| **Framework API** | FastAPI | - Performance élevée (async)<br>- Documentation auto (Swagger)<br>- Validation via Pydantic<br>- Standard moderne Python |
| **Modèle ML** | XGBoost | - Performance supérieure<br>- Gestion déséquilibre<br>- Compatible SHAP<br>- Rapide en inférence |
| **Interprétabilité** | SHAP | - Standard industrie<br>- Explications fiables<br>- TreeExplainer optimisé<br>- Top 5 features (~50ms) |
| **Base de données** | PostgreSQL (Supabase) | - SQL robuste et performant<br>- Hébergement cloud gratuit<br>- Async via asyncpg<br>- Migrations Alembic |
| **Déploiement** | Docker + HF Spaces | - Reproductibilité totale<br>- Gratuit et public<br>- CI/CD intégré<br>- URL stable |
| **Tests** | pytest + coverage | - 75 tests automatisés<br>- 76.68% de couverture<br>- CI obligatoire<br>- Qualité garantie |

---

## SLIDE 7 - Workflow Git et CI/CD

**Titre**: Stratégie Git et Pipeline CI/CD

**Git Workflow**:
```
main (production)
  │
  ├──► release/v1.0.x (hotfixes)
  │      │
  │      └──► PR merge ──► main
  │
  └──► feature/xxx (nouvelles features)
         │
         └──► PR merge ──► main
```

**Pipeline CI/CD** (GitHub Actions):
```
┌─────────────────┐
│  git push       │
│  to branch      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     GITHUB ACTIONS                      │
│                                         │
│  1. ┌────────────────────────────┐     │
│     │  Run Tests (pytest)        │     │
│     │  - 75 tests                │     │
│     │  - Coverage ≥ 75%          │     │
│     └────────┬───────────────────┘     │
│              │ ✓ PASS                  │
│              ▼                          │
│  2. ┌────────────────────────────┐     │
│     │  Test Database Integration │     │
│     │  - Supabase connection     │     │
│     └────────┬───────────────────┘     │
│              │ ✓ PASS                  │
│              ▼                          │
│  3. ┌────────────────────────────┐     │
│     │  Claude Code Review        │     │
│     │  - Quality checks          │     │
│     └────────┬───────────────────┘     │
│              │ ✓ PASS                  │
└──────────────┼─────────────────────────┘
               │
               ▼ (si merge sur main)
┌─────────────────────────────────────────┐
│     DEPLOY TO HF SPACES                 │
│     - Build Docker image                │
│     - Push to HF Space                  │
│     - Auto-deployment                   │
└─────────────────────────────────────────┘
```

**Avantages**:
- Zero-downtime deployment
- Tests automatiques obligatoires
- Review code automatique
- Traçabilité complète

---

## SLIDE 8 - Diagramme UML - Classes principales

**Titre**: Diagramme UML des Classes

```
┌─────────────────────────────────────────┐
│          ModelService                   │
├─────────────────────────────────────────┤
│ - model: Pipeline                       │
│ - metadata: Dict                        │
│ - feature_columns: Dict                 │
│ - explainer: TreeExplainer              │
├─────────────────────────────────────────┤
│ + load() -> bool                        │
│ + predict(data: Dict) -> Tuple         │
│ + predict_batch(List[Dict]) -> List    │
│ + explain(data: Dict) -> List[Dict]    │
│ + preprocess_input(Dict) -> DataFrame  │
│ - _get_risk_level(float) -> str        │
└──────────────┬──────────────────────────┘
               │
               │ uses
               ▼
┌─────────────────────────────────────────┐
│       EmployeeFeatures                  │
├─────────────────────────────────────────┤
│ + employee_id: Optional[str]            │
│ + age: int                              │
│ + revenu_mensuel: float                 │
│ + nombre_heures_travailless: int        │
│ + satisfaction_employee_*: int          │
│ + genre: str                            │
│ + statut_marital: str                   │
│ + departement: str                      │
│ + poste: str                            │
│ + ... (26 fields total)                 │
└──────────────┬──────────────────────────┘
               │
               │ validates
               ▼
┌─────────────────────────────────────────┐
│       PredictionResponse                │
├─────────────────────────────────────────┤
│ + prediction: PredictionResult          │
│ + metadata: Dict                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      ExplanationResponse                │
├─────────────────────────────────────────┤
│ + top_features: List[FeatureExplanation]│
│ + metadata: Dict                        │
└─────────────────────────────────────────┘
```

---

## SLIDE 9 - Fonctionnalités clés

**Titre**: Fonctionnalités Implémentées

**1. Prédiction simple** (`POST /api/v1/predict`)
```json
Input: {
  "age": 35,
  "revenu_mensuel": 5000,
  "satisfaction_employee_environnement": 4,
  ...
}

Output: {
  "prediction": {
    "will_leave": false,
    "probability_leave": 12.5,
    "probability_stay": 87.5,
    "risk_level": "LOW"
  },
  "metadata": { "prediction_time_ms": 25 }
}
```

**2. Prédiction batch** (`POST /api/v1/predict/batch`)
- Jusqu'à 100 employés simultanément
- Optimisation des performances
- Temps de réponse: <5s pour 10 employés

**3. Explications SHAP** (`POST /api/v1/explain`) ⭐ **Nouveauté v1.2.0**
```json
Output: {
  "top_features": [
    {
      "feature": "heure_supplementaires_Yes",
      "shap_value": 0.1523,
      "impact": "increases risk"
    },
    { "feature": "satisfaction_employee_environnement",
      "shap_value": -0.0654,
      "impact": "decreases risk"
    },
    ...
  ]
}
```

---

## SLIDE 10 - Qualité et tests

**Titre**: Assurance Qualité et Couverture de Tests

**Métriques de qualité**:
- ✅ **75 tests automatisés** (pytest)
- ✅ **76.68% de couverture de code**
- ✅ **Seuil minimum: 75%** (enforcement CI)
- ✅ **0 erreur en production**

**Types de tests**:
```
tests/
  ├─ test_api_integration.py      (16 tests)
  │   └─ Tests end-to-end des endpoints
  │
  ├─ test_api_contracts.py        (14 tests)
  │   └─ Validation des schemas Pydantic
  │
  ├─ test_model_service.py        (18 tests)
  │   └─ Logique métier du modèle
  │
  ├─ test_database.py             (2 tests)
  │   └─ Intégration base de données
  │
  ├─ test_api_errors.py           (6 tests)
  │   └─ Gestion des erreurs
  │
  ├─ test_model_edge_cases.py     (2 tests)
  │   └─ Cas limites
  │
  ├─ test_explain.py              (2 tests)
  │   └─ Explications SHAP
  │
  └─ ... (15 autres tests)
```

**Validation continue**:
- Pre-commit hooks (formatage, linting)
- CI obligatoire avant merge
- Review code automatique (Claude)

---

## SLIDE 11 - Évolutions par version

**Titre**: Historique des Versions

**v1.0.0** - API de base
- ✅ Endpoints de prédiction (simple + batch)
- ✅ Modèle XGBoost entraîné
- ✅ Déploiement Docker sur HF Spaces
- ✅ 65 tests, 75% couverture

**v1.0.2** - Intégration base de données
- ✅ PostgreSQL via Supabase
- ✅ Logs de toutes les prédictions
- ✅ Graceful degradation (API fonctionne sans BDD)
- ✅ Migrations Alembic

**v1.0.4** - Amélioration qualité
- ✅ Tests d'erreurs et edge cases
- ✅ Couverture: 75% → 76.68%
- ✅ Configuration .coveragerc
- ✅ Enforcement CI (min 75%)

**v1.2.0** - Interprétabilité ⭐ **Version actuelle**
- ✅ Endpoint `/api/v1/explain` (SHAP)
- ✅ Top 5 features influentes
- ✅ Temps de réponse: ~40-80ms
- ✅ 75 tests, documentation complète

---

## SLIDE 12 - Démo et accès

**Titre**: Démonstration et Liens

**🌐 API publique en production**:
```
https://ghislaindelabie-oc5-ml-api.hf.space
```

**📚 Documentation interactive**:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Landing page: `/`

**💻 Code source**:
```
github.com/ghislaindelabie/oc5-deploy-ml
```

**📊 Statistiques**:
- **Uptime**: 99.9% (Hugging Face Spaces)
- **Latence**: <100ms (prédictions simples)
- **Tests**: 75 tests, 76.68% couverture
- **Taille**: ~350KB (modèle), ~250MB (image Docker)

**🔑 Points forts**:
1. API REST production-ready
2. Interprétabilité via SHAP
3. Traçabilité complète (BDD)
4. CI/CD automatisé
5. Tests robustes
6. Documentation exhaustive

---

## Notes pour la présentation

### Diagrammes à insérer dans PowerPoint
Les diagrammes ASCII ci-dessus peuvent être:
1. **Copiés tels quels** avec police monospace (Courier New, Consolas)
2. **Recréés visuellement** avec les outils de dessin PowerPoint
3. **Remplacés par des images** générées avec draw.io ou Lucidchart

### Personnalisation suggérée
- Ajoutez des **captures d'écran** de l'API Swagger UI
- Incluez des **graphiques de performance** du modèle
- Montrez un **exemple de réponse SHAP** en direct
- Ajoutez votre **photo/logo** sur la page de titre

### Temps suggéré par slide
- Slides 1-2: 1-2 minutes (introduction)
- Slides 3-6: 5-6 minutes (architecture technique)
- Slides 7-8: 3-4 minutes (qualité et workflow)
- Slides 9-10: 3-4 minutes (fonctionnalités)
- Slides 11-12: 2-3 minutes (démonstration et conclusion)

**Total**: 15-20 minutes de présentation
