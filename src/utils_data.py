"""
Utility functions for data loading, cleaning, and exploratory prep.

Keep these lean: their job is to support notebooks, not replace them.
"""
from __future__ import annotations
from typing import Dict, Iterable, List, Tuple, Optional
import numpy as np
import pandas as pd
from collections import Counter
from typing import Tuple
import pandas as pd


def load_raw_sources(path_sirh: str, path_eval: str, path_survey: str) -> dict[str, pd.DataFrame]:
    """
    Load the three raw CSV files into DataFrames.

    Parameters
    ----------
    path_sirh : str
        Path to SIRH data file.
    path_eval : str
        Path to performance evaluation data file.
    path_survey : str
        Path to employee survey data file.

    Returns
    -------
    dict of str -> pd.DataFrame
        Dictionary with keys 'sirh', 'evals', 'survey'.
    """
    # Dummy safe version: just try reading, caller handles errors
    return {
        "sirh": pd.read_csv(path_sirh),
        "evals": pd.read_csv(path_eval),
        "survey": pd.read_csv(path_survey),
    }


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to snake_case, strip spaces.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Same DataFrame with renamed columns.
    """
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def build_central_df(sirh: pd.DataFrame, evals: pd.DataFrame, survey: pd.DataFrame) -> pd.DataFrame:
    """
    Join the three sources into one central DataFrame.
    
    - SIRH: has id_employee
    - Eval: has eval_number like 'E_1' (extract integer)
    - Survey: has code_sondage matching id_employee
    """
    evals = evals.copy()
    # Extract numeric part of eval_number to align with id_employee
    evals["id_employee"] = evals["eval_number"].str.extract(r"(\d+)").astype(int)
    
    # Survey already has code_sondage -> rename to id_employee for clarity
    survey = survey.rename(columns={"code_sondage": "id_employee"})
    
    # Merge everything on id_employee
    df = sirh.merge(evals, on="id_employee", how="left").merge(survey, on="id_employee", how="left")
    return df

def assess_missingness(
    df: pd.DataFrame,
    quasi_constant_threshold: float = 0.98,
    high_missing_threshold: float = 0.80,
    moderate_missing_threshold: float = 0.40,
) -> Dict[str, object]:
    """
    Profile missingness and low-variance columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe to analyze.
    quasi_constant_threshold : float, default 0.98
        Minimum ratio of the most frequent value to flag a column as quasi-constant.
    high_missing_threshold : float, default 0.80
        Fraction of missing values at/above which a column is flagged as high-missing.
    moderate_missing_threshold : float, default 0.40
        Fraction of missing values at/above which a column is flagged as moderate-missing.

    Returns
    -------
    Dict[str, object]
        {
          "profile": pd.DataFrame,       # one row per column with stats
          "constant_cols": List[str],
          "quasi_constant_cols": List[str],
          "high_missing_cols": List[str],
          "moderate_missing_cols": List[str]
        }
    """
    n_rows = len(df)

    # --- Missingness overview
    missing = df.isna().sum().to_frame("n_missing")
    missing["pct_missing"] = missing["n_missing"] / n_rows if n_rows else 0.0

    # --- True-constant columns (incl. all-NaN)
    nunique = df.nunique(dropna=False)
    constant_cols: List[str] = nunique[nunique <= 1].index.tolist()

    # --- Quasi-constant columns via dominance of top value
    def _top_ratio(s: pd.Series) -> float:
        if s.empty:
            return 1.0
        vc = s.value_counts(normalize=True, dropna=False)
        return float(vc.iloc[0]) if len(vc) else 1.0

    top_ratios = df.apply(_top_ratio)
    quasi_constant_cols = (
        top_ratios[top_ratios >= quasi_constant_threshold]
        .index.difference(constant_cols)
        .tolist()
    )

    # --- Build compact profiling table using value_counts()
    profile_rows = []
    for col in df.columns:
        vc = df[col].value_counts(dropna=False)
        first_val = vc.index[0] if len(vc) else np.nan
        first_cnt = int(vc.iloc[0]) if len(vc) else 0

        profile_rows.append({
            "column": col,
            "dtype": df[col].dtype,
            "nunique": int(nunique[col]),
            "n_missing": int(missing.loc[col, "n_missing"]),
            "pct_missing": float(missing.loc[col, "pct_missing"]),
            "top_value": first_val,
            "top_ratio": (first_cnt / n_rows) if n_rows else np.nan,
        })

    profile = pd.DataFrame(profile_rows).sort_values(
        ["pct_missing", "top_ratio"], ascending=[False, False]
    ).reset_index(drop=True)

    # --- Shortlists by thresholds
    high_missing_cols = missing.index[
        missing["pct_missing"] >= high_missing_threshold
    ].tolist()
    moderate_missing_cols = missing.index[
        (missing["pct_missing"] >= moderate_missing_threshold)
        & (missing["pct_missing"] < high_missing_threshold)
    ].tolist()

    return {
        "profile": profile,
        "constant_cols": constant_cols,
        "quasi_constant_cols": quasi_constant_cols,
        "high_missing_cols": high_missing_cols,
        "moderate_missing_cols": moderate_missing_cols,
    }

# A generic function to assess value frequencies in a column of a dataframe
def value_frequencies(
    df: pd.DataFrame,
    column: str,
    split: bool = False,
    sep: str = ","
) -> Tuple[int, pd.DataFrame]:
    """
    Compte les fréquences des valeurs d'une colonne.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame source.
    column : str
        Nom de la colonne à analyser.
    split : bool, default False
        Si True, on suppose que chaque cellule peut contenir
        plusieurs valeurs séparées par `sep`.
    sep : str, default ","
        Séparateur utilisé si split=True.

    Returns
    -------
    n_unique : int
        Nombre total de valeurs uniques.
    freq_df : pd.DataFrame
        Tableau trié par fréquence décroissante avec colonnes
        [<column>, "Frequency"].
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not in DataFrame")

    series = df[column].dropna().astype(str)

    # Aplatir si besoin
    if split:
        all_values = []
        for entry in series:
            parts = [v.strip() for v in entry.split(sep) if v.strip()]
            all_values.extend(parts)
    else:
        all_values = series.tolist()

    counter = Counter(all_values)
    total = sum(counter.values())

    freq_df = (
        pd.DataFrame(counter.items(), columns=[column, "Frequency"])
        .sort_values("Frequency", ascending=False)
        .reset_index(drop=True)
    )
    freq_df["Percentage"] = freq_df["Frequency"] / total * 100

    return freq_df.shape[0], freq_df


def attrition_rate_by_category(df: pd.DataFrame, cat_col: str, target: str = "a_quitte_l_entreprise") -> pd.DataFrame:
    """
    Calcule le taux de départ (cible == 'Oui') en fonction d'une variable catégorielle.

    Parameters
    ----------
    df : pd.DataFrame
        Le DataFrame central avec toutes les données.
    cat_col : str
        Le nom de la variable catégorielle.
    target : str, default 'a_quitte_l_entreprise'
        Le nom de la variable cible (doit être Oui/Non ou équivalent).

    Returns
    -------
    pd.DataFrame
        Tableau avec colonnes [cat_col, 'n', 'taux_depart'].
    """
    grouped = (
        df.groupby(cat_col)[target]
        .agg(n="count", taux_depart=lambda x: (x == "Oui").mean())
        .reset_index()
        .sort_values("taux_depart", ascending=False)
    )
    return grouped

def suggest_correlated_features(
    df: pd.DataFrame,
    cols: Optional[Iterable[str]] = None,
    *,
    threshold: float = 0.90,
    method: str = "pearson",
    protect: Optional[Iterable[str]] = None,
    return_pairs: bool = False,
) -> Tuple[List[str], Optional[pd.DataFrame]]:
    """
    Suggest a list of numeric features to drop based on a correlation threshold.
    Greedy rule: for each correlated pair, drop the column with the higher
    mean absolute correlation to others (more redundant). 'protect' columns are never dropped.
    """
    if cols is None:
        cols = df.select_dtypes(include="number").columns.tolist()
    else:
        cols = [c for c in cols if c in df.columns]
    cols = list(dict.fromkeys(cols))

    if len(cols) <= 1:
        return [], (pd.DataFrame(columns=["col_i","col_j","abs_corr"]) if return_pairs else None)

    corr = df[cols].corr(method=method).abs()
    np.fill_diagonal(corr.values, 0.0)

    iu = np.triu_indices_from(corr, k=1)
    pairs = [(cols[i], cols[j], corr.iat[i, j]) for i, j in zip(*iu) if corr.iat[i, j] >= threshold]
    if not pairs:
        return [], (pd.DataFrame(columns=["col_i","col_j","abs_corr"]) if return_pairs else None)

    pairs_df = pd.DataFrame(pairs, columns=["col_i","col_j","abs_corr"]).sort_values("abs_corr", ascending=False)

    mean_abs = corr.mean(axis=0)
    to_drop: set = set()
    protected = set(protect or [])

    for _, row in pairs_df.iterrows():
        a, b = row["col_i"], row["col_j"]
        if a in to_drop or b in to_drop:
            continue
        if a in protected and b in protected:
            continue
        if a in protected:
            to_drop.add(b); continue
        if b in protected:
            to_drop.add(a); continue
        drop_candidate = a if mean_abs[a] >= mean_abs[b] else b
        to_drop.add(drop_candidate)

    drop_list = [c for c in cols if c in to_drop]
    return (drop_list, pairs_df) if return_pairs else (drop_list, None)

def split_feature_types(df: pd.DataFrame, target: str) -> tuple[list[str], list[str]]:
    """
    Split features into numeric and categorical lists.

    Parameters
    ----------
    df : pd.DataFrame
    target : str
        Name of the target column.

    Returns
    -------
    (numeric_features, categorical_features)
    """
    num_cols = df.drop(columns=[target]).select_dtypes(include="number").columns.tolist()
    cat_cols = df.drop(columns=[target]).select_dtypes(exclude="number").columns.tolist()
    return num_cols, cat_cols