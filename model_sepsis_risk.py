"""
NeoGuardian - Machine Learning Sepsis Risk Modeling
Trains predictive models on neonatal clinical features, vital signs, and device exposure
to estimate:
  1) Culture-Confirmed / Severe Sepsis Risk
  2) 30-Day Mortality Risk
Provides feature importance rankings to guide clinical decision support in the NICU.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support


DATA_PATH = os.path.join("data", "sepsis", "neonatal_sepsis.csv")


def load_and_preprocess():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    feature_cols = [
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

    # Target 1: Proven or Severe Sepsis (Group 1 or Culture Positive)
    y_sepsis = ((df["sepsis_group"] == 1) | (df["blood_culture_positive"] == 1)).astype(int)

    # Target 2: 30-day mortality
    y_mortality = df["overall_mortality_within_30_days"].astype(int)

    X = df[feature_cols].copy()

    # Impute missing values with median
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols)

    return X_imputed, y_sepsis, y_mortality, feature_cols


def evaluate_task(task_name, X, y, feature_names):
    print("\n" + "=" * 65)
    print(f" TASK: {task_name.upper()}")
    print("=" * 65)
    print(f"Total samples: {len(y):,} | Positive cases: {y.sum():,} ({y.mean() * 100:.2f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression (Balanced)": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, solver="lbfgs", random_state=42))
        ]),
        "Random Forest (Balanced)": RandomForestClassifier(
            n_estimators=150, class_weight="balanced", max_depth=6, random_state=42
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.08, max_depth=3, random_state=42
        ),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    best_model_name = None
    best_auc = 0.0
    best_fitted_model = None

    for name, model in models.items():
        auc_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        mean_auc = np.mean(auc_scores)
        std_auc = np.std(auc_scores)
        print(f"\nModel: {name}")
        print(f"  • 5-Fold Cross-Validation ROC-AUC: {mean_auc:.3f} (+/- {std_auc:.3f})")

        # Fit on train and evaluate on holdout test set
        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
        test_auc = roc_auc_score(y_test, y_prob)
        p, r, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", zero_division=0)
        print(f"  • Holdout Test Set ROC-AUC:        {test_auc:.3f}")
        print(f"  • Precision: {p:.3f} | Recall: {r:.3f} | F1-Score: {f1:.3f}")

        if test_auc > best_auc:
            best_auc = test_auc
            best_model_name = name
            best_fitted_model = model

    # Feature importances from Random Forest
    rf_model = models["Random Forest (Balanced)"]
    if hasattr(rf_model, "feature_importances_"):
        importances = rf_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        print(f"\nTop Predictive Features (Random Forest):")
        print("-" * 55)
        for rank, idx in enumerate(indices[:8], 1):
            clean_name = feature_names[idx].replace("_", " ").title()
            print(f"  {rank:2d}. {clean_name:<38}: {importances[idx]:.4f}")


def main():
    X, y_sepsis, y_mortality, features = load_and_preprocess()
    evaluate_task("1. Culture-Confirmed / Proven Sepsis Risk Prediction", X, y_sepsis, features)
    evaluate_task("2. 30-Day Neonatal Mortality Risk Prediction", X, y_mortality, features)
    print("\n" + "=" * 65)
    print(" Sepsis ML risk modeling evaluation completed successfully.")
    print("=" * 65)


if __name__ == "__main__":
    main()
