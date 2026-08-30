"""
NeoGuardian Model Training Script
Trains scikit-learn Random Forest models for:
  1. Culture-Confirmed Sepsis Risk Prediction
  2. 30-Day Neonatal Mortality Risk Prediction
Initializes and serializes real TreeSHAP explainers for local feature attribution.
Saves artifacts to backend/app/models/*.joblib for low-latency API inference.
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score


FEATURE_NAMES = [
    "gestational_age_at_birth_weeks",
    "birth_weight_kg",
    "sex",
    "onset_age_in_days",
    "onset_hour_of_day",
    "temp_celsius",
    "intubated_at_time_of_sepsis_evaluation",
    "inotrope_at_time_of_sepsis_eval",
    "central_venous_line",
    "umbilical_arterial_line",
    "ecmo",
    "comorbidity_necrotizing_enterocolitis",
    "comorbidity_chronic_lung_disease",
    "comorbidity_cardiac",
    "comorbidity_surgical",
    "comorbidity_ivh_or_shunt",
]


def train_and_save():
    print("=" * 65)
    print("  NEOGUARDIAN - TRAINING SEPSIS & MORTALITY ML MODELS WITH SHAP")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))

    data_path = os.path.join(project_root, "data", "sepsis", "neonatal_sepsis.csv")
    if not os.path.exists(data_path):
        alt_path = os.path.join(project_root, "data", "sepsis", "deid-nicu-sepsis-tta.csv")
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            raise FileNotFoundError(f"Sepsis dataset not found at {data_path}")

    print(f"Loading clinical training cohort from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df):,} evaluation records.")

    # Targets
    y_sepsis = ((df["sepsis_group"] == 1) | (df["blood_culture_positive"] == 1)).astype(int).values
    y_mortality = df["overall_mortality_within_30_days"].astype(int).values

    # Features
    X_raw = df[FEATURE_NAMES].copy()
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X_raw), columns=FEATURE_NAMES)

    models_dir = os.path.join(base_dir, "app", "models")
    os.makedirs(models_dir, exist_ok=True)

    # 1. Train Sepsis Risk Model
    print("\n[1/4] Training Sepsis Risk Random Forest Classifier...")
    rf_sepsis = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        class_weight="balanced",
        random_state=42
    )
    rf_sepsis.fit(X_imputed, y_sepsis)
    sepsis_auc = roc_auc_score(y_sepsis, rf_sepsis.predict_proba(X_imputed)[:, 1])
    print(f"      • Training ROC-AUC: {sepsis_auc:.3f}")

    sepsis_model_file = os.path.join(models_dir, "sepsis_risk_model.joblib")
    joblib.dump(rf_sepsis, sepsis_model_file)
    print(f"      • Saved model to: {sepsis_model_file}")

    # 2. Train Mortality Risk Model
    print("\n[2/4] Training 30-Day Mortality Random Forest Classifier...")
    rf_mortality = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        class_weight="balanced",
        random_state=42
    )
    rf_mortality.fit(X_imputed, y_mortality)
    mortality_auc = roc_auc_score(y_mortality, rf_mortality.predict_proba(X_imputed)[:, 1])
    print(f"      • Training ROC-AUC: {mortality_auc:.3f}")

    mortality_model_file = os.path.join(models_dir, "mortality_risk_model.joblib")
    joblib.dump(rf_mortality, mortality_model_file)
    print(f"      • Saved model to: {mortality_model_file}")

    # 3. Create and Serialize Sepsis TreeSHAP Explainer
    print("\n[3/4] Initializing TreeSHAP Explainer for Sepsis Model...")
    explainer_sepsis = shap.TreeExplainer(rf_sepsis)
    sepsis_explainer_file = os.path.join(models_dir, "sepsis_shap_explainer.joblib")
    joblib.dump(explainer_sepsis, sepsis_explainer_file)
    print(f"      • Saved SHAP explainer to: {sepsis_explainer_file}")

    # 4. Create and Serialize Mortality TreeSHAP Explainer
    print("\n[4/4] Initializing TreeSHAP Explainer for Mortality Model...")
    explainer_mortality = shap.TreeExplainer(rf_mortality)
    mortality_explainer_file = os.path.join(models_dir, "mortality_shap_explainer.joblib")
    joblib.dump(explainer_mortality, mortality_explainer_file)
    print(f"      • Saved SHAP explainer to: {mortality_explainer_file}")

    # Save imputer as well for consistent inference
    imputer_file = os.path.join(models_dir, "feature_imputer.joblib")
    joblib.dump(imputer, imputer_file)
    print(f"      • Saved feature imputer to: {imputer_file}")

    print("\n" + "=" * 65)
    print("  MODEL TRAINING & SHAP SERIALIZATION COMPLETE!")
    print("=" * 65)


if __name__ == "__main__":
    train_and_save()
