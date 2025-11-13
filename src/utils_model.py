from __future__ import annotations
from typing import List, Optional, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import CountVectorizer

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import make_scorer, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score


from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict


from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.utils.validation import check_is_fitted

from imblearn.pipeline import Pipeline as ImbPipeline


def make_preprocessor(
    single_cat_cols: List[str],
    num_cols: List[str],
    *,
    multi_list_col: Optional[str] = None,
    max_categories: int = 30,
    multi_max_features: int = 30,
    onehot_drop_binary: bool = True,
    onehot_sparse: bool = True,
):
    """
    Build a ColumnTransformer that:
      - One-hots single-valued categorical columns (drops one level if binary).
      - Vectorizes an optional multi-valued list column (comma-separated) with CountVectorizer (binary).
      - Imputes numerics with median.
    Notes:
      - Pass your own column lists. Columns absent in the DataFrame will be ignored by ColumnTransformer at fit time.
      - If you have binary categorical columns (e.g., Oui/Non, M/F), include them in single_cat_cols:
        OneHotEncoder(drop='if_binary') will keep only 1 column per binary feature.

    Returns
    -------
    sklearn.compose.ColumnTransformer
    """

    # 1) Single-valued categoricals → OneHot
    ohe = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        max_categories=max_categories,
        drop="if_binary" if onehot_drop_binary else None,
        sparse_output=onehot_sparse,
    )
    cat_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", ohe),
    ])

    # 2) Optional multi-valued (comma-separated) → CountVectorizer(binary)
    multiuse_pipe = None
    if multi_list_col:
        multiuse_pipe = Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value="")),
            # flatten (n_samples, 1) -> (n_samples,)
            ("flatten", FunctionTransformer(lambda x: x.ravel(), feature_names_out="one-to-one")),
            ("vectorize", CountVectorizer(
                tokenizer=lambda s: [t.strip() for t in s.split(",") if t.strip()],
                token_pattern=None,
                lowercase=False,
                binary=True,
                max_features=multi_max_features,
            )),
        ])

    # 3) Numerics → median impute
    num_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
    ])

    transformers = []
    if single_cat_cols:
        transformers.append(("cats", cat_pipe, single_cat_cols))
    if multiuse_pipe:
        transformers.append(("multiuse", multiuse_pipe, [multi_list_col]))
    if num_cols:
        transformers.append(("num", num_pipe, num_cols))

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=True,
    )
    return preprocessor

def make_preprocessors_for_smote(
    single_cat_cols: List[str],
    num_cols: List[str],
    *,
    multi_list_col: Optional[str] = None,
    max_categories: int = 30,
    multi_max_features: int = 30,
    onehot_drop_binary: bool = True,
    onehot_sparse: bool = True,
):
    """
    Create two preprocessors:
      - prep_sample: uses dense output for SMOTE compatibility
      - prep_model: normal sparse/dense encoder for model training
    Returns (prep_sample, prep_model, cat_mask)
    """

    from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import CountVectorizer

    # --- Base categorical pipeline
    ohe_dense = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        max_categories=max_categories,
        drop="if_binary" if onehot_drop_binary else None,
        sparse_output=False,  # dense for SMOTE
    )
    ohe_user = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        max_categories=max_categories,
        drop="if_binary" if onehot_drop_binary else None,
        sparse_output=onehot_sparse,
    )

    cat_pipe_dense = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", ohe_dense),
    ])
    cat_pipe_user = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", ohe_user),
    ])

    # --- Multi-valued list column (optional)
    multi_pipe = None
    if multi_list_col:
        multi_pipe = Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value="")),
            ("flatten", FunctionTransformer(lambda x: x.ravel(), feature_names_out="one-to-one")),
            ("vectorize", CountVectorizer(
                tokenizer=lambda s: [t.strip() for t in s.split(",") if t.strip()],
                token_pattern=None,
                lowercase=False,
                binary=True,
                max_features=multi_max_features,
            )),
        ])

    # --- Numeric pipeline
    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median"))])

    # --- Combine all
    def build_transformer(cat_pipe):
        transformers = []
        if single_cat_cols:
            transformers.append(("cats", cat_pipe, single_cat_cols))
        if multi_pipe:
            transformers.append(("multiuse", multi_pipe, [multi_list_col]))
        if num_cols:
            transformers.append(("num", num_pipe, num_cols))
        return ColumnTransformer(transformers=transformers, remainder="drop")

    prep_sample = build_transformer(cat_pipe_dense)
    prep_model = build_transformer(cat_pipe_user)

    # --- cat_mask: True for each categorical feature
    cat_mask = [False] * len(num_cols) + [True] * len(single_cat_cols)
    return prep_sample, prep_model, cat_mask

# This section provides functions for classification and running models



def _default_classifiers() -> Dict[str, object]:
    """Return a minimal set of baseline classifiers with standard params."""
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    models = {
        "Dummy(stratified)": DummyClassifier(strategy="stratified", random_state=42),
        # no n_jobs param for LogReg in many versions; liblinear is stable for binary
        "LogReg": LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear"),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, random_state=42, class_weight="balanced_subsample", n_jobs=-1
        ),
    }
    # Optional: XGBoost if present
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            random_state=42,
            n_estimators=300,
            learning_rate=0.1,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            eval_metric="logloss",
            tree_method="hist",
        )
        models["XGBoost_enhanced"] = XGBClassifier(
            random_state=42,
            n_estimators=200,
            learning_rate=0.1,
            reg_alpha = 1,
            reg_lambda = 5,
            scale_pos_weight = 1, # Original coefficient on imbalanced dataset was 5.2025316455696204. Now not useful
            max_depth=7,
            subsample=0.7,
            colsample_bytree=1,
            min_child_weight = 3,
            n_jobs=-1,
            eval_metric="logloss",
            tree_method="hist",
        )
    except Exception:
        pass
    return models


def quick_cv_models(
    preprocessor,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    cv_splits: int = 5,
    n_jobs: int = -1,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Run a quick cross-validated comparison of default classifiers with the given preprocessor.

    Scorers: accuracy, precision, recall, f1, roc_auc, average_precision (PR AUC).
    Returns a DataFrame sorted by average_precision (higher is better).
    """
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)

    scorers = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "avg_precision": "average_precision",  # PR AUC
    }

    rows = []
    for name, clf in _default_classifiers().items():
        pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
        scores = cross_validate(
            pipe,
            X,
            y,
            scoring=scorers,
            cv=skf,
            n_jobs=n_jobs,
            return_train_score=False,
            error_score="raise",
        )
        rows.append(
            {
                "model": name,
                "accuracy_mean": scores["test_accuracy"].mean(),
                "precision_mean": scores["test_precision"].mean(),
                "recall_mean": scores["test_recall"].mean(),
                "f1_mean": scores["test_f1"].mean(),
                "roc_auc_mean": scores["test_roc_auc"].mean(),
                "avg_precision_mean": scores["test_avg_precision"].mean(),
                "fit_time_s": np.mean(scores["fit_time"]),
                "score_time_s": np.mean(scores["score_time"]),
            }
        )

    df = pd.DataFrame(rows).sort_values("avg_precision_mean", ascending=False).reset_index(drop=True)
    return df



# reuse your _default_classifiers()
# def _default_classifiers() -> Dict[str, object]: ... (already defined above)

def oof_probas(
    preprocessor,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    cv_splits: int = 5,
    n_jobs: int = -1,
    random_state: int = 42,
) -> Dict[str, np.ndarray]:
    """
    Return out-of-fold positive-class probabilities for each default classifier.
    Uses cross_val_predict(..., method='predict_proba') inside StratifiedKFold.
    """
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
    out = {}
    for name, clf in _default_classifiers().items():
        pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
        # prefer predict_proba; if not available, fall back to decision_function
        method = "predict_proba" if hasattr(clf, "predict_proba") else "decision_function"
        preds = cross_val_predict(
            pipe, X, y, cv=skf, method=method, n_jobs=n_jobs
        )
        # convert to positive-class probability if predict_proba
        if method == "predict_proba":
            preds = preds[:, 1]
        # decision_function can be any real value; for PR/ROC curves, raw scores are acceptable.
        out[name] = preds
    return out

def make_prec_at_recall_floor(floor: float = 0.80):
    """
    Return a sklearn scorer that:
      - calls estimator.predict(X)
      - computes recall; if recall < floor -> returns 0.0
      - otherwise returns precision
    Use this when you want to maximize precision subject to a minimum recall.
    """
    def _score(y_true, y_pred):
        rec = recall_score(y_true, y_pred)
        if rec < floor:
            return 0.0
        return precision_score(y_true, y_pred)
    return make_scorer(_score, greater_is_better=True)

    
class GateRankClassifier(BaseEstimator, ClassifierMixin):
    """
    Two-stage classifier:
      - gate_estimator produces p_gate = P(y=1 | x)
      - If p_gate >= gate_threshold => 'positive side' scored by pos_estimator
        else 'negative side' scored by neg_estimator
      - Predict uses top-@ for each side (fractions in [0,1])
      - predict_proba returns the fused score used on each side (discontinuous at the threshold)
    """

    def __init__(self,
                 gate_estimator=None,
                 pos_estimator=None,
                 neg_estimator=None,
                 gate_threshold: float = 0.35,
                 top_pos: float = 0.25,
                 top_neg: float = 0.1,
                 random_state: int= 42):
        # store args verbatim; do not instantiate here
        self.gate_estimator = gate_estimator
        self.pos_estimator = pos_estimator
        self.neg_estimator = neg_estimator
        self.gate_threshold = float(gate_threshold)
        self.top_pos = float(top_pos)
        self.top_neg = float(top_neg)
        self.random_state = random_state


    
    def fit(self, X, y):
        # lazy import to avoid import-time costs
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier

        # IMPORTANT: never use `or` with estimator objects (truthiness triggers __len__).
        if self.gate_estimator is None:
            gate = LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear",
                                      random_state=self.random_state)
        else:
            gate = self.gate_estimator

        if self.pos_estimator is None:
            pos = RandomForestClassifier(n_estimators=300, random_state=self.random_state,
                                         class_weight="balanced_subsample", n_jobs=-1)
        else:
            pos = self.pos_estimator

        if self.neg_estimator is None:
            neg = RandomForestClassifier(n_estimators=300, random_state=self.random_state,
                                         class_weight="balanced_subsample", n_jobs=-1)
        else:
            neg = self.neg_estimator

        # clone before fitting to play nice with GridSearch/clone()
        self.gate_ = clone(gate).fit(X, y)
        self.pos_  = clone(pos ).fit(X, y)
        self.neg_  = clone(neg ).fit(X, y)
        return self

    def _scores(self, X):
        check_is_fitted(self, ["gate_", "pos_", "neg_"])
        p_gate = self.gate_.predict_proba(X)[:, 1]
        n = p_gate.shape[0]
        pos_mask = p_gate >= self.gate_threshold
        neg_mask = ~pos_mask

        p_pos = np.zeros(n, dtype=float)
        p_neg = np.zeros(n, dtype=float)

        if np.any(pos_mask):
            idx_pos = np.flatnonzero(pos_mask)
            X_pos = X.iloc[idx_pos] if hasattr(X, "iloc") else X[idx_pos]
            p_pos[idx_pos] = self.pos_.predict_proba(X_pos)[:, 1]

        if np.any(neg_mask):
            idx_neg = np.flatnonzero(neg_mask)
            X_neg = X.iloc[idx_neg] if hasattr(X, "iloc") else X[idx_neg]
            p_neg[idx_neg] = self.neg_.predict_proba(X_neg)[:, 1]

        return p_gate, p_pos, p_neg

    def predict(self, X):
        p_gate, p_pos, p_neg = self._scores(X)
        n = len(p_gate)
        yhat = np.zeros(n, dtype=int)

        pos_idx = np.flatnonzero(p_gate >= self.gate_threshold)
        neg_idx = np.flatnonzero(p_gate <  self.gate_threshold)

        if len(pos_idx):
            k_pos = int(np.floor(self.top_pos * len(pos_idx)))
            if k_pos > 0:
                order_pos = pos_idx[np.argsort(-p_pos[pos_idx])]
                yhat[order_pos[:k_pos]] = 1

        if len(neg_idx):
            k_neg = int(np.floor(self.top_neg * len(neg_idx)))
            if k_neg > 0:
                order_neg = neg_idx[np.argsort(-p_neg[neg_idx])]
                yhat[order_neg[:k_neg]] = 1

        return yhat
"""
    def predict_proba(self, X):
        # fused (discontinuous) score: ranker score from the side you belong to
        p_gate, p_pos, p_neg = self._scores(X)
        s = np.where(p_gate >= self.gate_threshold, p_pos, p_neg)
        s = np.clip(s, 0.0, 1.0)
        proba = np.vstack([1.0 - s, s]).T
        return proba
"""

# This section provides functions to use resampling and handle class imbalances
# ===== Imbalanced-learning CV helpers =====
def _require_imblearn():
    try:
        import imblearn  # noqa: F401
        from imblearn.pipeline import Pipeline as ImbPipeline  # noqa: F401
        return True
    except Exception as e:
        raise ImportError(
            "This feature requires `imbalanced-learn`.\n"
            "Install it and retry, e.g. with: `uv add --no-build imbalanced-learn`"
        ) from e


def make_samplers(basic: bool = True):
    """
    Build a small, robust palette of samplers.
    Returns a dict: {name: sampler_instance}
    """
    _require_imblearn()
    from imblearn.under_sampling import RandomUnderSampler, NearMiss
    from imblearn.over_sampling import RandomOverSampler, SMOTE
    from imblearn.combine import SMOTETomek

    samplers = {}

    
    # ---- NONE = BASELINE
    samplers["None"] = None
    # ---- UNDERSAMPLING
    samplers["Under:Random"] = RandomUnderSampler(random_state=42)
    # NearMiss is more aggressive; keep version small to avoid too many failures
    samplers["Under:NearMiss1"] = NearMiss(version=1)

    # ---- OVERSAMPLING
    samplers["Over:Random"] = RandomOverSampler(random_state=42)
    # SMOTE can fail if k_neighbors >= minority count; keep conservative
    samplers["Over:SMOTE"] = SMOTE(random_state=42, k_neighbors=3)

    # ---- HYBRID
    # Hybrid (SMOTE + Tomek links) is a good out-of-the-box combo
    samplers["Hybrid:SMOTE+Tomek"] = SMOTETomek(random_state=42, smote=SMOTE(random_state=42, k_neighbors=3))

    if not basic:
        
        # I can add more variants here later if I want
        pass

    return samplers


def make_sampling_pipeline(preprocessor, sampler, classifier):
    """
    Create an imblearn Pipeline: preprocessor -> [sampler(s)] -> classifier.

    `sampler` can be:
      - None (no sampling)
      - a single sampler (fit_resample)
      - a list of (name, step) tuples (e.g., SMOTE then UnderSampler)
    """
    _require_imblearn()
    from imblearn.pipeline import Pipeline as ImbPipeline

    steps = [("prep", preprocessor)]

    if sampler is None:
        pass
    elif isinstance(sampler, list):
        # Expect list of (name, estimator) tuples
        for tup in sampler:
            if not (isinstance(tup, tuple) and len(tup) == 2):
                raise TypeError("sampler list must be a list of (name, estimator) tuples")
        steps.extend(sampler)
    else:
        # Single sampler estimator
        steps.append(("sampler", sampler))

    steps.append(("clf", classifier))
    return ImbPipeline(steps)


def quick_cv_models_with_sampling(
    preprocessor,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    samplers: Optional[Dict[str, object]] = None,
    classifiers: Optional[Dict[str, object]] = None,
    cv_splits: int = 5,
    n_jobs: int = -1,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Cross-validate a grid of (sampler × classifier) with the same scorers
    used by quick_cv_models, and return a tidy DataFrame.

    Notes
    -----
    - Uses imblearn.Pipeline so resampling happens **inside** each fold only.
    - Safe defaults for scorers (accuracy, precision, recall, f1, roc_auc, average_precision).
    """
    _require_imblearn()
    from sklearn.model_selection import StratifiedKFold, cross_validate

    if samplers is None:
        samplers = make_samplers(basic=True)

    if classifiers is None:
        classifiers = _default_classifiers()

    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)

    scorers = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "avg_precision": "average_precision",
    }

    rows = []
    for s_name, sampler in samplers.items():
        for m_name, clf in classifiers.items():
            pipe = make_sampling_pipeline(preprocessor, sampler, clf)
            scores = cross_validate(
                pipe,
                X,
                y,
                scoring=scorers,
                cv=skf,
                n_jobs=n_jobs,
                return_train_score=False,
                error_score="raise",
            )
            rows.append(
                {
                    "sampler": s_name,
                    "model": m_name,
                    "accuracy_mean": scores["test_accuracy"].mean(),
                    "precision_mean": scores["test_precision"].mean(),
                    "recall_mean": scores["test_recall"].mean(),
                    "f1_mean": scores["test_f1"].mean(),
                    "roc_auc_mean": scores["test_roc_auc"].mean(),
                    "avg_precision_mean": scores["test_avg_precision"].mean(),
                    "fit_time_s": float(np.mean(scores["fit_time"])),
                    "score_time_s": float(np.mean(scores["score_time"])),
                }
            )

    df = pd.DataFrame(rows).sort_values(
        ["avg_precision_mean", "recall_mean"], ascending=[False, False]
    ).reset_index(drop=True)
    return df


def cross_val_threshold_metrics(
    preprocessor,
    clf,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    thresholds: Optional[List[float]] = None,
    cv_splits: int = 5,
    n_jobs: int = -1,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Helper to pick a decision threshold using out-of-fold probabilities.

    - Computes OOF positive scores via cross_val_predict(predict_proba).
    - Evaluates precision/recall/F1 for a list of thresholds.
    - Returns a small DataFrame to help you choose a threshold.

    This ignores samplers on purpose (pure classifier behavior).
    If you need samplers, wrap `clf` in an imblearn pipeline before passing here.
    """
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    if thresholds is None:
        thresholds = [0.2, 0.3, 0.35, 0.4, 0.5]

    pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)

    # OOF probabilities
    if hasattr(clf, "predict_proba"):
        oof = cross_val_predict(pipe, X, y, cv=skf, method="predict_proba", n_jobs=n_jobs)[:, 1]
    else:
        # fallback: decision_function → min-max scale to [0,1] for a crude thresholding
        raw = cross_val_predict(pipe, X, y, cv=skf, method="decision_function", n_jobs=n_jobs)
        rmin, rmax = np.min(raw), np.max(raw)
        oof = (raw - rmin) / (rmax - rmin + 1e-12)

    out = []
    for t in thresholds:
        yhat = (oof >= t).astype(int)
        out.append({
            "threshold": t,
            "precision": precision_score(y, yhat, zero_division=0),
            "recall": recall_score(y, yhat, zero_division=0),
            "f1": f1_score(y, yhat, zero_division=0),
        })
    return pd.DataFrame(out).sort_values("threshold")

