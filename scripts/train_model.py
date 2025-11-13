"""
Training Script for HR Attrition Model

This script extracts the logic from 02_modeling_eval_explain.ipynb
and trains the final XGBoost Enhanced model.

Purpose:
    - Load raw data from data/ directory
    - Apply preprocessing (drop correlated features, encode, impute)
    - Train XGBoost Enhanced classifier with optimized hyperparameters
    - Save trained pipeline to model/ directory
    - Save metadata (features, metrics, version)

Usage:
    python scripts/train_model.py

Output:
    - model/hr_attrition_xgb_enhanced.joblib (trained pipeline)
    - model/feature_metadata.json (feature names, version, metrics)
    - model/training_report.txt (human-readable summary)

Dependencies:
    - src/utils_data.py (data loading, preprocessing)
    - src/utils_model.py (preprocessor creation)
    - artifacts/correlated_features.json (features to drop)

Model Configuration (from notebook analysis):
    XGBClassifier:
        n_estimators: 200
        learning_rate: 0.1
        max_depth: 7
        min_child_weight: 3
        subsample: 0.7
        colsample_bytree: 1.0
        reg_alpha: 1
        reg_lambda: 5
        scale_pos_weight: 1.0
        eval_metric: "logloss"
        tree_method: "hist"
        random_state: 42

Expected Performance:
    - Precision @ 50% Recall: ~0.625
    - ROC AUC: ~0.75
    - PR AUC: ~0.52

TODO:
    - Import necessary libraries (pandas, sklearn, xgboost, joblib)
    - Load data using utils_data.load_raw_sources()
    - Build central dataframe using utils_data.build_central_df()
    - Load correlated features from artifacts/
    - Create preprocessor using utils_model.make_preprocessor()
    - Define XGBoost classifier with params above
    - Create sklearn Pipeline
    - Train on full dataset (or train/val split if validating)
    - Cross-validate to verify metrics
    - Save pipeline and metadata
"""

# CODE TO BE WRITTEN IN PHASE 0
