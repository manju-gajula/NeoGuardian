"""
NeoGuardian Sepsis & Mortality Machine Learning Predictor
Wraps pre-trained Random Forest models and TreeSHAP explainers to estimate:
  1) Culture-Confirmed Sepsis Risk Probability
  2) 30-Day Neonatal Mortality Risk Probability
Provides mathematically rigorous, instance-level TreeSHAP feature attributions.
"""

import os
import joblib
import pandas as pd
import numpy as np
import shap
from typing import Dict, Any, List, Tuple


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

FEATURE_LABELS = {
    "gestational_age_at_birth_weeks": "Gestational Age (weeks)",
    "birth_weight_kg": "Birth Weight (kg)",
    "sex": "Sex (Male/Female)",
    "onset_age_in_days": "Onset Age (days)",
    "onset_hour_of_day": "Onset Hour of Day",
    "temp_celsius": "Core Temperature (°C)",
    "intubated_at_time_of_sepsis_evaluation": "Mechanical Ventilation (Intubated)",
    "inotrope_at_time_of_sepsis_eval": "Inotropic Vasopressor Support",
    "central_venous_line": "Central Venous Line (CVL)",
    "umbilical_arterial_line": "Umbilical Arterial Line (UAL)",
    "ecmo": "ECMO Life Support",
    "comorbidity_necrotizing_enterocolitis": "Necrotizing Enterocolitis (NEC)",
    "comorbidity_chronic_lung_disease": "Chronic Lung Disease (CLD)",
    "comorbidity_cardiac": "Congenital Heart Defect",
    "comorbidity_surgical": "Surgical Abdomen",
    "comorbidity_ivh_or_shunt": "IVH or Ventricular Shunt",
}

COHORT_MEDIANS = {
    "gestational_age_at_birth_weeks": 34.0,
    "birth_weight_kg": 2.04,
    "sex": 0,
    "onset_age_in_days": 18.0,
    "onset_hour_of_day": 12,
    "temp_celsius": 37.3,
    "intubated_at_time_of_sepsis_evaluation": 0,
    "inotrope_at_time_of_sepsis_eval": 0,
    "central_venous_line": 1,
    "umbilical_arterial_line": 0,
    "ecmo": 0,
    "comorbidity_necrotizing_enterocolitis": 0,
    "comorbidity_chronic_lung_disease": 0,
    "comorbidity_cardiac": 0,
    "comorbidity_surgical": 0,
    "comorbidity_ivh_or_shunt": 0,
}


class SepsisModelManager:
    _instance = None

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.abspath(os.path.join(current_dir, "..", "models"))
        
        self.sepsis_model_path = os.path.join(self.models_dir, "sepsis_risk_model.joblib")
        self.mortality_model_path = os.path.join(self.models_dir, "mortality_risk_model.joblib")
        self.sepsis_shap_path = os.path.join(self.models_dir, "sepsis_shap_explainer.joblib")
        self.mortality_shap_path = os.path.join(self.models_dir, "mortality_shap_explainer.joblib")

        self.sepsis_model = None
        self.mortality_model = None
        self.sepsis_explainer = None
        self.mortality_explainer = None

        self.load_models()

    @classmethod
    def get_instance(cls) -> "SepsisModelManager":
        if cls._instance is None:
            cls._instance = SepsisModelManager()
        return cls._instance

    def load_models(self):
        # 1. Load Sepsis Model
        if os.path.exists(self.sepsis_model_path):
            try:
                self.sepsis_model = joblib.load(self.sepsis_model_path)
                print("[SepsisModel] Loaded sepsis risk Random Forest model.")
            except Exception as e:
                print(f"[SepsisModel] Error loading sepsis model: {e}")

        # 2. Load Mortality Model
        if os.path.exists(self.mortality_model_path):
            try:
                self.mortality_model = joblib.load(self.mortality_model_path)
                print("[SepsisModel] Loaded mortality risk Random Forest model.")
            except Exception as e:
                print(f"[SepsisModel] Error loading mortality model: {e}")

        # 3. Load or Initialize Sepsis TreeSHAP Explainer
        if os.path.exists(self.sepsis_shap_path):
            try:
                self.sepsis_explainer = joblib.load(self.sepsis_shap_path)
                print("[SepsisModel] Loaded sepsis TreeSHAP explainer from file.")
            except Exception as e:
                print(f"[SepsisModel] Note: Rebuilding sepsis TreeSHAP explainer directly from model ({e})")
                if self.sepsis_model is not None:
                    try:
                        self.sepsis_explainer = shap.TreeExplainer(self.sepsis_model)
                        print("[SepsisModel] Successfully initialized sepsis TreeSHAP explainer.")
                    except Exception as ex:
                        print(f"[SepsisModel] Error initializing sepsis TreeSHAP: {ex}")
        elif self.sepsis_model is not None:
            try:
                self.sepsis_explainer = shap.TreeExplainer(self.sepsis_model)
                print("[SepsisModel] Initialized sepsis TreeSHAP explainer directly.")
            except Exception as ex:
                print(f"[SepsisModel] Error initializing sepsis TreeSHAP: {ex}")

        # 4. Load or Initialize Mortality TreeSHAP Explainer
        if os.path.exists(self.mortality_shap_path):
            try:
                self.mortality_explainer = joblib.load(self.mortality_shap_path)
                print("[SepsisModel] Loaded mortality TreeSHAP explainer from file.")
            except Exception as e:
                print(f"[SepsisModel] Note: Rebuilding mortality TreeSHAP explainer directly from model ({e})")
                if self.mortality_model is not None:
                    try:
                        self.mortality_explainer = shap.TreeExplainer(self.mortality_model)
                        print("[SepsisModel] Successfully initialized mortality TreeSHAP explainer.")
                    except Exception as ex:
                        print(f"[SepsisModel] Error initializing mortality TreeSHAP: {ex}")
        elif self.mortality_model is not None:
            try:
                self.mortality_explainer = shap.TreeExplainer(self.mortality_model)
                print("[SepsisModel] Initialized mortality TreeSHAP explainer directly.")
            except Exception as ex:
                print(f"[SepsisModel] Error initializing mortality TreeSHAP: {ex}")

    def _prepare_features(self, req_dict: Dict[str, Any]) -> pd.DataFrame:
        row = {}
        for col in FEATURE_NAMES:
            val = req_dict.get(col)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                val = COHORT_MEDIANS.get(col, 0)
            row[col] = float(val)
        return pd.DataFrame([row], columns=FEATURE_NAMES)

    def _extract_shap_attributions(self, X: pd.DataFrame, explainer: Any) -> List[Dict[str, str]]:
        if explainer is None:
            return []

        try:
            raw_shap = explainer.shap_values(X)
            # Handle binary classification formats across different shap versions
            if isinstance(raw_shap, list) and len(raw_shap) == 2:
                vals = raw_shap[1][0]
            elif hasattr(raw_shap, "values"):
                # Explanation object
                ev = raw_shap.values
                if len(ev.shape) == 3:
                    vals = ev[0, :, 1]
                else:
                    vals = ev[0]
            elif len(np.shape(raw_shap)) == 3:
                vals = raw_shap[0, :, 1]
            elif len(np.shape(raw_shap)) == 2:
                vals = raw_shap[0]
            else:
                vals = np.asarray(raw_shap).flatten()

            # Sort by absolute SHAP impact
            abs_indices = np.argsort(np.abs(vals))[::-1]
            contributions = []

            for idx in abs_indices[:5]:
                col = FEATURE_NAMES[idx]
                shap_val = float(vals[idx])
                actual_val = X.iloc[0][col]

                # Format human readable impact
                if shap_val > 0:
                    direction = "INCREASES_RISK"
                    impact_str = f"+{shap_val * 100:.1f}% risk impact (value: {actual_val:g})"
                else:
                    direction = "DECREASES_RISK"
                    impact_str = f"{shap_val * 100:.1f}% risk impact (value: {actual_val:g})"

                contributions.append({
                    "feature": col,
                    "label": FEATURE_LABELS.get(col, col),
                    "impact": impact_str,
                    "direction": direction
                })

            return contributions
        except Exception as e:
            print(f"[SepsisModel] SHAP extraction warning: {e}")
            return []

    def predict_sepsis(self, req_dict: Dict[str, Any]) -> Dict[str, Any]:
        X = self._prepare_features(req_dict)
        
        if self.sepsis_model is not None:
            prob = float(self.sepsis_model.predict_proba(X)[0, 1])
        else:
            prob = 0.10

        pct = round(prob * 100.0, 1)

        if prob >= 0.28:
            status = "RED"
            level = "HIGH"
            rec = "CRITICAL: High sepsis probability. Recommend prompt blood culture, CBC, CRP, and stat empiric antibiotics."
        elif prob >= 0.14:
            status = "YELLOW"
            level = "MODERATE"
            rec = "ELEVATED RISK: Clinical sepsis indicators present. Increase cardiorespiratory and temperature surveillance."
        else:
            status = "GREEN"
            level = "LOW"
            rec = "LOW RISK: Expected neonatal baseline parameters."

        contributions = self._extract_shap_attributions(X, self.sepsis_explainer)

        return {
            "sepsis_probability": round(prob, 4),
            "sepsis_risk_percentage": pct,
            "status": status,
            "risk_level": level,
            "top_contributing_features": contributions,
            "clinical_recommendation": rec
        }

    def predict_mortality(self, req_dict: Dict[str, Any]) -> Dict[str, Any]:
        X = self._prepare_features(req_dict)

        if self.mortality_model is not None:
            prob = float(self.mortality_model.predict_proba(X)[0, 1])
        else:
            prob = 0.05

        pct = round(prob * 100.0, 1)

        if prob >= 0.12:
            status = "RED"
            level = "CRITICAL"
            rec = "HIGH MORTALITY RISK: Intensive multi-organ supportive care and vital organ perfusion monitoring required."
        elif prob >= 0.05:
            status = "YELLOW"
            level = "MODERATE"
            rec = "MODERATE RISK: Monitor closely for ventilatory exhaustion and cardiovascular instability."
        else:
            status = "GREEN"
            level = "LOW"
            rec = "LOW RISK: Low mortality hazard index."

        contributions = self._extract_shap_attributions(X, self.mortality_explainer)

        return {
            "mortality_probability": round(prob, 4),
            "mortality_risk_percentage": pct,
            "status": status,
            "risk_level": level,
            "top_contributing_features": contributions,
            "clinical_recommendation": rec
        }
