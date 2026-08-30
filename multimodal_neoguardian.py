"""
NeoGuardian - Multimodal Neonatal Cardiorespiratory & Sepsis Risk Integration
Connects the PICSDB cardiorespiratory stream (Apnea & Bradycardia events)
with the clinical Sepsis Risk & Decompensation Profile.

Clinical Principle:
In preterm infants, sudden increases in apnea/bradycardia frequency, loss of heart rate
variability, and temperature instability are classical precursors to late-onset sepsis (LOS).
"""

import os
import pandas as pd
import numpy as np


def load_sepsis_cohort():
    path = os.path.join("data", "sepsis", "neonatal_sepsis.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sepsis dataset not found at {path}")
    return pd.read_csv(path)


def compute_neonatal_decompensation_score(
    apnea_events_per_hour: float,
    min_heart_rate_bpm: float,
    temp_celsius: float,
    gestational_age_weeks: float,
    birth_weight_kg: float,
    central_line: bool = True,
    intubated: bool = False
):
    """
    Computes a composite Neonatal Decompensation & Sepsis Alert Score (0 - 100).
    Higher scores indicate higher risk of clinical decompensation and underlying sepsis.
    """
    score = 0.0

    # 1. Cardiorespiratory Component (PICSDB stream derived)
    if apnea_events_per_hour >= 4.0:
        score += 25.0
    elif apnea_events_per_hour >= 2.0:
        score += 15.0
    elif apnea_events_per_hour >= 1.0:
        score += 8.0

    if min_heart_rate_bpm < 80.0:
        score += 25.0  # Severe bradycardia
    elif min_heart_rate_bpm < 100.0:
        score += 15.0  # Moderate bradycardia
    elif min_heart_rate_bpm < 120.0:
        score += 5.0

    # 2. Temperature Stability
    if temp_celsius < 36.5:
        score += 18.0  # Neonatal hypothermia (strongly correlated with sepsis)
    elif temp_celsius >= 38.0:
        score += 14.0  # Fever

    # 3. Prematurity & Vulnerability
    if gestational_age_weeks < 28.0:
        score += 12.0  # Extremely preterm
    elif gestational_age_weeks < 32.0:
        score += 8.0   # Very preterm

    if birth_weight_kg < 1.0:
        score += 10.0  # Extremely low birth weight
    elif birth_weight_kg < 1.5:
        score += 6.0   # Very low birth weight

    # 4. Invasive Device & Support Exposure
    if central_line:
        score += 6.0
    if intubated:
        score += 4.0

    score = min(100.0, score)

    # Triage classification
    if score >= 65.0:
        triage = "CRITICAL: HIGH SEPSIS / DECOMPENSATION RISK (Urgent Blood Culture & Workup Recommended)"
        color = "RED"
    elif score >= 40.0:
        triage = "ELEVATED RISK: Close Cardiorespiratory & Septic Screening Monitoring"
        color = "YELLOW"
    else:
        triage = "STABLE: Routine Neonatal Care"
        color = "GREEN"

    return score, triage, color


def main():
    print("=" * 70)
    print("  NEOGUARDIAN MULTIMODAL PLATFORM: CARDIORESPIRATORY + SEPSIS PIPELINE")
    print("=" * 70)

    # 1. Inspect Sepsis Dataset
    df_sepsis = load_sepsis_cohort()
    print(f"\n[1] Clinical Sepsis Cohort Loaded:")
    print(f"    • Total episodes: {len(df_sepsis):,} across {df_sepsis['unique_patient_id'].nunique():,} neonates.")
    print(f"    • Preterm patients (<37 weeks): {(df_sepsis['gestational_age_at_birth_weeks'] < 37).sum():,} ({(df_sepsis['gestational_age_at_birth_weeks'] < 37).mean()*100:.1f}%)")

    # 2. Inspect PICSDB Signals Available
    picsdb_dir = os.path.join("data", "picsdb")
    if os.path.exists(picsdb_dir):
        records = [f.replace(".hea", "") for f in os.listdir(picsdb_dir) if f.endswith("_resp.hea")]
        print(f"\n[2] PICSDB Waveform Records Available ({len(records)} subjects):")
        print(f"    • Subjects: {', '.join(sorted(records))}")

    # 3. Demonstrate Integrated Neonatal Monitoring Scenarios
    print("\n[3] Simulated Multimodal Clinical Scenarios:")
    print("-" * 70)

    scenarios = [
        {
            "case": "Patient A (Infant 1 - Extreme Preterm with Recurrent Apnea/Brady Spells)",
            "apnea_per_hr": 3.8,
            "min_hr": 78.0,
            "temp": 36.3,
            "ga": 26.0,
            "bw": 0.85,
            "cvl": True,
            "intubated": True
        },
        {
            "case": "Patient B (Infant with Isolated Mild Periodic Breathing)",
            "apnea_per_hr": 0.8,
            "min_hr": 115.0,
            "temp": 37.1,
            "ga": 34.0,
            "bw": 2.10,
            "cvl": False,
            "intubated": False
        },
        {
            "case": "Patient C (Late Preterm with Late Onset Fever & Tachy/Brady)",
            "apnea_per_hr": 2.2,
            "min_hr": 92.0,
            "temp": 38.6,
            "ga": 33.0,
            "bw": 1.75,
            "cvl": True,
            "intubated": False
        }
    ]

    for sc in scenarios:
        score, triage, color = compute_neonatal_decompensation_score(
            apnea_events_per_hour=sc["apnea_per_hr"],
            min_heart_rate_bpm=sc["min_hr"],
            temp_celsius=sc["temp"],
            gestational_age_weeks=sc["ga"],
            birth_weight_kg=sc["bw"],
            central_line=sc["cvl"],
            intubated=sc["intubated"]
        )
        print(f"\nScenario: {sc['case']}")
        print(f"  • Vital Stats: GA={sc['ga']}wks | BW={sc['bw']}kg | Temp={sc['temp']}°C")
        print(f"  • Cardiorespiratory: Apneas={sc['apnea_per_hr']}/hr | Min HR={sc['min_hr']} BPM")
        print(f"  • Decompensation Score: {score:.1f} / 100 [{color}]")
        print(f"  • Clinical Recommendation: {triage}")

    print("\n" + "=" * 70)
    print(" Multimodal cardiorespiratory-sepsis integration demonstration complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
