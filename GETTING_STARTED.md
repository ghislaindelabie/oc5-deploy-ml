# Getting Started - OC5 ML Deployment Project

## ✅ Project Setup Complete!

The project structure has been created with placeholder files and copied dependencies from OC4.

## 📂 What Was Created

### New Directories:
- **`scripts/`** - Model training scripts
- **`model/`** - Will contain trained model artifacts
- **`data/`** - Raw HR data files (copied from OC4)
- **`db/`** - Database setup scripts
- **`artifacts/`** - Training artifacts (feature lists, etc.)

### New Files (all with TODO comments):
- `scripts/train_model.py` - Extract notebook logic, train XGBoost Enhanced
- `app/schemas.py` - Pydantic models for API validation
- `app/model_service.py` - Model loading and prediction logic
- `app/database.py` - PostgreSQL ORM setup
- `db/schema.sql` - Database schema
- `db/create_db.py` - Python database creation
- `tests/test_api.py` - FastAPI endpoint tests
- `tests/test_model_service.py` - Model service unit tests

### Copied from OC4:
- ✅ `data/extrait_sirh.csv` (94 KB)
- ✅ `data/extrait_eval.csv` (43 KB)
- ✅ `data/extrait_sondage.csv` (83 KB)
- ✅ `src/utils_data.py` (10 KB)
- ✅ `src/utils_model.py` (23 KB)
- ✅ `artifacts/correlated_features.json` (130 B)

## 🎯 Next Steps - Phased Approach

### Phase 0: Model Preparation (START HERE)
**Goal**: Train and save the XGBoost Enhanced model

**Tasks**:
1. **Write `scripts/train_model.py`** (skeleton exists with detailed TODOs)
   - Load data using `utils_data.load_raw_sources()`
   - Build central dataframe with `utils_data.build_central_df()`
   - Create preprocessor with `utils_model.make_preprocessor()`
   - Define XGBoost with hyperparameters from notebook
   - Train pipeline on full dataset
   - Save to `model/hr_attrition_xgb_enhanced.joblib`

2. **Run training**:
   ```bash
   python scripts/train_model.py
   ```

3. **Verify outputs**:
   - `model/hr_attrition_xgb_enhanced.joblib` exists (~5-20 MB)
   - `model/feature_metadata.json` exists
   - Check metrics match notebook (~0.625 precision @ 50% recall)

**Deliverable**: Trained model artifact ready for API integration

---

### Phase 1: API Development
**Goal**: Create FastAPI endpoints that load model and serve predictions

**Files to implement** (skeletons exist):
1. `app/schemas.py` - Define EmployeeInput and PredictionOutput
2. `app/model_service.py` - Load model, make predictions
3. Update `app/main.py` - Add `/predict` endpoint

**Testing**:
```bash
uvicorn app.main:app --reload
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @sample_input.json
```

---

### Phase 2: PostgreSQL Integration
**Files to implement**:
1. `db/schema.sql` - CREATE TABLE predictions
2. `db/create_db.py` - Automated database setup
3. `app/database.py` - SQLAlchemy models and session

**Setup**:
```bash
# Start PostgreSQL (Docker recommended)
docker run --name oc5-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres

# Create database
python db/create_db.py
```

---

### Phase 3: Testing
**Files to implement**:
1. `tests/test_model_service.py` - Unit tests for model
2. `tests/test_api.py` - Integration tests for API

**Run tests**:
```bash
pytest -v --cov=app --cov=src
```

---

### Phase 4-6: Documentation, CI/CD, Presentation
Follow workplan in analysis document.

---

## 📋 File Reference

### Where to Find What:

| Need | File Location |
|------|---------------|
| **Preprocessing logic** | `src/utils_data.py`, `src/utils_model.py` |
| **Training params** | `scripts/train_model.py` (comments list all params) |
| **Feature names** | `artifacts/correlated_features.json` (dropped features) |
| **Data schema** | `data/README.md` |
| **API schemas** | `app/schemas.py` (26 input features listed in comments) |
| **Database schema** | `db/schema.sql` |
| **Model metadata** | `model/README.md` |

### Each Placeholder File Contains:
- **Purpose**: What it does
- **TODO**: Step-by-step implementation guide
- **Examples**: Code patterns to follow
- **Dependencies**: What imports are needed

---

## 🔍 Quick Verification

Check that everything is in place:

```bash
# Data files
ls -lh data/*.csv

# Utility functions
ls -lh src/utils_*.py

# Placeholder files
ls -lh scripts/*.py app/*.py db/*.{sql,py} tests/*.py

# Artifacts
cat artifacts/correlated_features.json
```

---

## 💡 Development Tips

1. **Start with Phase 0**: You CANNOT proceed without a trained model
2. **Read the TODO comments**: Each file has detailed implementation notes
3. **Use the OC4 notebook**: Reference `/Users/.../oc4-hr-attrition/02_modeling_eval_explain.ipynb`
4. **Test incrementally**: Run training → test prediction → integrate API
5. **Follow the workplan**: Phases are designed to minimize rework

---

## 🤝 Need Help?

Each file's header comment explains:
- What the file should do
- How to implement it
- What dependencies it needs
- Expected inputs/outputs

Start with `scripts/train_model.py` - it has the most detailed guide!

---

**Status**: 🟢 Ready for Phase 0 - Model Training

**Next Action**: Open `scripts/train_model.py` and start implementing the training logic!
