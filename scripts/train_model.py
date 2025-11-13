"""
Training Script for HR Attrition Model

Extracts logic from 02_modeling_eval_explain.ipynb and trains
the final XGBoost Enhanced model.

Author: Ghislain Delabie
Date: 2024-11-13
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate, StratifiedKFold
from xgboost import XGBClassifier

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils_data import load_raw_sources, build_central_df
from utils_model import make_preprocessor


def main():
    """Main training pipeline"""

    print("=" * 70)
    print("HR ATTRITION MODEL TRAINING")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # =========================================================================
    # 1. LOAD DATA
    # =========================================================================
    print("📂 Loading raw data files...")

    data_dir = Path(__file__).parent.parent / "data"

    raw_data = load_raw_sources(
        path_sirh=str(data_dir / "extrait_sirh.csv"),
        path_eval=str(data_dir / "extrait_eval.csv"),
        path_survey=str(data_dir / "extrait_sondage.csv")
    )

    print(f"  ✓ SIRH: {len(raw_data['sirh'])} rows")
    print(f"  ✓ Evaluations: {len(raw_data['evals'])} rows")
    print(f"  ✓ Survey: {len(raw_data['survey'])} rows")

    # =========================================================================
    # 2. BUILD CENTRAL DATAFRAME
    # =========================================================================
    print("\n🔗 Merging data sources...")

    base_HR = build_central_df(
        raw_data['sirh'],
        raw_data['evals'],
        raw_data['survey']
    )

    print(f"  ✓ Central dataframe: {base_HR.shape[0]} rows × {base_HR.shape[1]} columns")

    # =========================================================================
    # 3. LOAD CORRELATED FEATURES TO DROP
    # =========================================================================
    print("\n📋 Loading feature configuration...")

    artifacts_dir = Path(__file__).parent.parent / "artifacts"

    try:
        with open(artifacts_dir / "correlated_features.json", "r") as f:
            correlated_features = json.load(f)
        print(f"  ✓ Will drop {len(correlated_features)} correlated features:")
        for feat in correlated_features:
            print(f"    - {feat}")
    except FileNotFoundError:
        correlated_features = []
        print("  ⚠ No correlated_features.json found, using all features")

    # =========================================================================
    # 4. PREPARE TARGET AND FEATURES
    # =========================================================================
    print("\n🎯 Preparing features and target...")

    target = "a_quitte_l_entreprise"

    # Map target to 0/1
    if base_HR[target].dtype == "object":
        base_HR[target] = base_HR[target].map({"Oui": 1, "Non": 0})

    y = base_HR[target]
    X = base_HR.drop(columns=[target, "id_employee"], errors="ignore")

    print(f"  ✓ Features: {X.shape[1]} columns")
    print(f"  ✓ Target distribution:")
    print(f"    - Class 0 (Stayed): {(y == 0).sum()} ({(y == 0).mean():.1%})")
    print(f"    - Class 1 (Left): {(y == 1).sum()} ({(y == 1).mean():.1%})")

    # =========================================================================
    # 5. DEFINE FEATURE TYPES
    # =========================================================================
    print("\n🏷️  Defining feature types...")

    # Categorical columns (single-valued)
    single_cat_cols = [
        "genre", "statut_marital", "departement", "poste",
        "domaine_etude", "heure_supplementaires"
    ]
    single_cat_cols = [c for c in single_cat_cols if c in X.columns]

    # Numeric columns (excluding correlated features)
    num_cols = X.select_dtypes(include="number").columns.tolist()
    num_cols = [c for c in num_cols if c not in correlated_features]

    print(f"  ✓ Categorical features: {len(single_cat_cols)}")
    print(f"  ✓ Numeric features: {len(num_cols)} (after dropping correlated)")
    print(f"  ✓ Total features for training: {len(single_cat_cols) + len(num_cols)}")

    # =========================================================================
    # 6. CREATE PREPROCESSOR
    # =========================================================================
    print("\n⚙️  Building preprocessor...")

    preprocessor = make_preprocessor(
        single_cat_cols=single_cat_cols,
        num_cols=num_cols,
        multi_list_col=None,  # No multi-valued columns in this dataset
        max_categories=30,
        multi_max_features=30,
        onehot_drop_binary=True,
        onehot_sparse=True
    )

    # Quick test to get feature names
    _ = preprocessor.fit_transform(X.head(100))
    feature_names_out = preprocessor.get_feature_names_out()
    print(f"  ✓ Preprocessor created: {len(feature_names_out)} features after encoding")

    # =========================================================================
    # 7. CREATE XGBOOST MODEL (Enhanced params from notebook)
    # =========================================================================
    print("\n🤖 Creating XGBoost Enhanced classifier...")

    xgb_clf = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=7,
        min_child_weight=3,
        subsample=0.7,
        colsample_bytree=1.0,
        reg_alpha=1,
        reg_lambda=5,
        scale_pos_weight=1.0,
        eval_metric="logloss",
        tree_method="hist",
        random_state=42,
        n_jobs=-1
    )

    print("  ✓ Hyperparameters:")
    print(f"    - n_estimators: 200")
    print(f"    - learning_rate: 0.1")
    print(f"    - max_depth: 7")
    print(f"    - min_child_weight: 3")
    print(f"    - subsample: 0.7")
    print(f"    - reg_alpha: 1, reg_lambda: 5")

    # =========================================================================
    # 8. CREATE PIPELINE
    # =========================================================================
    print("\n🔧 Building final pipeline...")

    pipeline = Pipeline([
        ("prep", preprocessor),
        ("clf", xgb_clf)
    ])

    print("  ✓ Pipeline: Preprocessor → XGBoost")

    # =========================================================================
    # 9. CROSS-VALIDATE TO VERIFY PERFORMANCE
    # =========================================================================
    print("\n📊 Running 5-fold cross-validation (this may take a minute)...")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    scorers = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "avg_precision": "average_precision"
    }

    cv_results = cross_validate(
        pipeline, X, y,
        scoring=scorers,
        cv=cv,
        n_jobs=-1,
        return_train_score=False
    )

    print("\n  ✓ Cross-validation results (mean ± std):")
    print(f"    - Accuracy:       {cv_results['test_accuracy'].mean():.3f} ± {cv_results['test_accuracy'].std():.3f}")
    print(f"    - Precision:      {cv_results['test_precision'].mean():.3f} ± {cv_results['test_precision'].std():.3f}")
    print(f"    - Recall:         {cv_results['test_recall'].mean():.3f} ± {cv_results['test_recall'].std():.3f}")
    print(f"    - F1-Score:       {cv_results['test_f1'].mean():.3f} ± {cv_results['test_f1'].std():.3f}")
    print(f"    - ROC AUC:        {cv_results['test_roc_auc'].mean():.3f} ± {cv_results['test_roc_auc'].std():.3f}")
    print(f"    - PR AUC:         {cv_results['test_avg_precision'].mean():.3f} ± {cv_results['test_avg_precision'].std():.3f}")
    print(f"    - Fit time (avg): {cv_results['fit_time'].mean():.2f}s")

    # =========================================================================
    # 10. TRAIN ON FULL DATASET
    # =========================================================================
    print("\n🎓 Training on full dataset...")

    pipeline.fit(X, y)

    print("  ✓ Model trained successfully!")

    # =========================================================================
    # 11. SAVE MODEL
    # =========================================================================
    print("\n💾 Saving model artifacts...")

    model_dir = Path(__file__).parent.parent / "model"
    model_dir.mkdir(exist_ok=True)

    # Save pipeline
    model_path = model_dir / "hr_attrition_xgb_enhanced.joblib"
    joblib.dump(pipeline, model_path)
    print(f"  ✓ Model saved: {model_path}")

    # =========================================================================
    # 12. SAVE METADATA
    # =========================================================================
    metadata = {
        "model_version": "xgb_enhanced_v1.0",
        "training_date": datetime.now().isoformat(),
        "dataset": {
            "n_samples": len(X),
            "n_features_raw": X.shape[1],
            "n_features_encoded": len(feature_names_out),
            "class_balance": {
                "class_0_stayed": int((y == 0).sum()),
                "class_1_left": int((y == 1).sum()),
                "attrition_rate": float(y.mean())
            }
        },
        "features": {
            "categorical": single_cat_cols,
            "numeric": num_cols,
            "dropped_correlated": correlated_features,
            "total_input": len(single_cat_cols) + len(num_cols)
        },
        "hyperparameters": {
            "n_estimators": 200,
            "learning_rate": 0.1,
            "max_depth": 7,
            "min_child_weight": 3,
            "subsample": 0.7,
            "colsample_bytree": 1.0,
            "reg_alpha": 1,
            "reg_lambda": 5,
            "scale_pos_weight": 1.0,
            "random_state": 42
        },
        "performance_cv": {
            "accuracy_mean": float(cv_results['test_accuracy'].mean()),
            "accuracy_std": float(cv_results['test_accuracy'].std()),
            "precision_mean": float(cv_results['test_precision'].mean()),
            "precision_std": float(cv_results['test_precision'].std()),
            "recall_mean": float(cv_results['test_recall'].mean()),
            "recall_std": float(cv_results['test_recall'].std()),
            "f1_mean": float(cv_results['test_f1'].mean()),
            "f1_std": float(cv_results['test_f1'].std()),
            "roc_auc_mean": float(cv_results['test_roc_auc'].mean()),
            "roc_auc_std": float(cv_results['test_roc_auc'].std()),
            "pr_auc_mean": float(cv_results['test_avg_precision'].mean()),
            "pr_auc_std": float(cv_results['test_avg_precision'].std())
        }
    }

    metadata_path = model_dir / "feature_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✓ Metadata saved: {metadata_path}")

    # =========================================================================
    # 13. SAVE TRAINING REPORT
    # =========================================================================
    report_path = model_dir / "training_report.txt"
    with open(report_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("HR ATTRITION MODEL - TRAINING REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model Version: xgb_enhanced_v1.0\n\n")

        f.write("DATASET\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Samples: {len(X)}\n")
        f.write(f"Features (raw): {X.shape[1]}\n")
        f.write(f"Features (encoded): {len(feature_names_out)}\n")
        f.write(f"Class 0 (Stayed): {(y == 0).sum()} ({(y == 0).mean():.1%})\n")
        f.write(f"Class 1 (Left): {(y == 1).sum()} ({(y == 1).mean():.1%})\n\n")

        f.write("CROSS-VALIDATION RESULTS (5-fold)\n")
        f.write("-" * 70 + "\n")
        f.write(f"Accuracy:    {cv_results['test_accuracy'].mean():.3f} ± {cv_results['test_accuracy'].std():.3f}\n")
        f.write(f"Precision:   {cv_results['test_precision'].mean():.3f} ± {cv_results['test_precision'].std():.3f}\n")
        f.write(f"Recall:      {cv_results['test_recall'].mean():.3f} ± {cv_results['test_recall'].std():.3f}\n")
        f.write(f"F1-Score:    {cv_results['test_f1'].mean():.3f} ± {cv_results['test_f1'].std():.3f}\n")
        f.write(f"ROC AUC:     {cv_results['test_roc_auc'].mean():.3f} ± {cv_results['test_roc_auc'].std():.3f}\n")
        f.write(f"PR AUC:      {cv_results['test_avg_precision'].mean():.3f} ± {cv_results['test_avg_precision'].std():.3f}\n\n")

        f.write("HYPERPARAMETERS\n")
        f.write("-" * 70 + "\n")
        for k, v in metadata["hyperparameters"].items():
            f.write(f"{k}: {v}\n")
        f.write("\n")

        f.write("FILES GENERATED\n")
        f.write("-" * 70 + "\n")
        f.write(f"Model: {model_path.name}\n")
        f.write(f"Metadata: {metadata_path.name}\n")
        f.write(f"Report: {report_path.name}\n")

    print(f"  ✓ Report saved: {report_path}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nModel saved to: {model_path.relative_to(Path.cwd())}")
    print(f"Expected performance: ~{cv_results['test_precision'].mean():.1%} precision @ ~{cv_results['test_recall'].mean():.1%} recall")
    print("\nNext steps:")
    print("  1. Test model loading: python -c \"import joblib; m = joblib.load('model/hr_attrition_xgb_enhanced.joblib'); print('✓ Model loads successfully')\"")
    print("  2. Review metadata: cat model/feature_metadata.json")
    print("  3. Commit and push changes")
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
