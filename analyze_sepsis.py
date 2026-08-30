"""
NeoGuardian - Neonatal Sepsis Analysis Module
Analyzes the clinical NICU sepsis evaluation cohort (deid-nicu-sepsis-tta.csv)
focusing on preterm risk factors, early vs. late onset sepsis, vital signs,
invasive device exposure, and mortality outcomes.
"""

import os
import pandas as pd
import numpy as np


DATA_PATH = os.path.join("data", "sepsis", "neonatal_sepsis.csv")
ALT_DATA_PATH = os.path.join("data", "sepsis", "deid-nicu-sepsis-tta.csv")


def load_dataset():
    path = DATA_PATH if os.path.exists(DATA_PATH) else ALT_DATA_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sepsis dataset not found at {DATA_PATH} or {ALT_DATA_PATH}")
    print(f"Loading neonatal sepsis dataset from: {path}")
    df = pd.read_csv(path)
    return df


def analyze_cohort(df):
    print("=" * 65)
    print("           NEOGUARDIAN - NEONATAL SEPSIS COHORT ANALYSIS")
    print("=" * 65)

    total_episodes = len(df)
    unique_patients = df["unique_patient_id"].nunique()
    print(f"Total Sepsis Evaluation Episodes: {total_episodes:,}")
    print(f"Unique Neonatal Patients:         {unique_patients:,}")
    print(f"Episodes per Patient (mean):       {total_episodes / unique_patients:.2f}")

    # Demographics & Prematurity
    print("\n" + "-" * 65)
    print("1. DEMOGRAPHICS & GESTATIONAL PREMATURITY")
    print("-" * 65)
    ga = df["gestational_age_at_birth_weeks"].dropna()
    bw = df["birth_weight_kg"].dropna()

    print(f"Gestational Age (weeks):  Median = {ga.median():.1f} | IQR = [{ga.quantile(0.25):.1f} - {ga.quantile(0.75):.1f}] | Min-Max = [{ga.min():.0f} - {ga.max():.0f}]")
    print(f"Birth Weight (kg):        Median = {bw.median():.2f} | IQR = [{bw.quantile(0.25):.2f} - {bw.quantile(0.75):.2f}] | Min-Max = [{bw.min():.2f} - {bw.max():.2f}]")

    preterm_count = (ga < 37).sum()
    very_preterm = (ga < 32).sum()
    extremely_preterm = (ga < 28).sum()
    vlbw = (bw < 1.5).sum()
    elbw = (bw < 1.0).sum()

    print(f"  • Preterm (< 37 wks):            {preterm_count:4d} ({preterm_count / len(ga) * 100:.1f}%)")
    print(f"  • Very Preterm (< 32 wks):       {very_preterm:4d} ({very_preterm / len(ga) * 100:.1f}%)")
    print(f"  • Extremely Preterm (< 28 wks):  {extremely_preterm:4d} ({extremely_preterm / len(ga) * 100:.1f}%)")
    print(f"  • Very Low Birth Weight (<1.5kg): {vlbw:4d} ({vlbw / len(bw) * 100:.1f}%)")
    print(f"  • Extremely Low BW (<1.0kg):     {elbw:4d} ({elbw / len(bw) * 100:.1f}%)")

    # Early-Onset vs Late-Onset Sepsis
    print("\n" + "-" * 65)
    print("2. ONSET CLASSIFICATION (EARLY vs. LATE ONSET SEPSIS)")
    print("-" * 65)
    eos_mask = df["onset_age_in_days"] <= 3
    los_mask = df["onset_age_in_days"] > 3
    eos_count = eos_mask.sum()
    los_count = los_mask.sum()

    print(f"Early-Onset Sepsis (EOS, <= 3 days):  {eos_count:4d} ({eos_count / total_episodes * 100:.1f}%)")
    print(f"Late-Onset Sepsis  (LOS, > 3 days):   {los_count:4d} ({los_count / total_episodes * 100:.1f}%)")

    # Sepsis Groups & Culture Results
    print("\n" + "-" * 65)
    print("3. CLINICAL SEPSIS GROUPS & MICROBIOLOGY")
    print("-" * 65)
    group_labels = {
        1: "Group 1: Proven Sepsis (Blood Culture Positive)",
        2: "Group 2: Rule-Out / Unproven Sepsis (Antibiotics stopped)",
        3: "Group 3: Clinical Sepsis (Culture Neg, Prolonged Abx)",
        4: "Group 4: Local Infection (UTI, CSF, Wound, etc.)",
        5: "Group 5: Viral Infection",
        6: "Group 6: Necrotizing Enterocolitis (NEC) / Abdominal"
    }
    for grp, count in df["sepsis_group"].value_counts().sort_index().items():
        label = group_labels.get(grp, f"Group {grp}")
        print(f"  • {label:<50}: {count:4d} ({count / total_episodes * 100:5.1f}%)")

    pos_culture = df["blood_culture_positive"].sum()
    print(f"\nBlood Culture Confirmed Positive: {pos_culture} ({pos_culture / total_episodes * 100:.1f}%)")

    # Critical Physiological & Vital Signs at Evaluation
    print("\n" + "-" * 65)
    print("4. PHYSIOLOGICAL SIGNS & INVASIVE SUPPORT AT SEPSIS EVALUATION")
    print("-" * 65)
    temps = df["temp_celsius"].dropna()
    hypothermia = (temps < 36.5).sum()
    fever = (temps >= 38.0).sum()
    normothermia = len(temps) - hypothermia - fever

    print(f"Temperature at Evaluation: Median = {temps.median():.1f}°C, IQR = [{temps.quantile(0.25):.1f} - {temps.quantile(0.75):.1f}]")
    print(f"  • Hypothermia (< 36.5°C):       {hypothermia:4d} ({hypothermia / len(temps) * 100:5.1f}%)")
    print(f"  • Fever (>= 38.0°C):            {fever:4d} ({fever / len(temps) * 100:5.1f}%)")
    print(f"  • Normothermia (36.5 - 37.9°C): {normothermia:4d} ({normothermia / len(temps) * 100:5.1f}%)")

    intubated = df["intubated_at_time_of_sepsis_evaluation"].sum()
    inotropes = df["inotrope_at_time_of_sepsis_eval"].sum()
    cvl = df["central_venous_line"].sum()
    ual = df["umbilical_arterial_line"].sum()

    print(f"\nInvasive Interventions Active at Sepsis Onset:")
    print(f"  • Intubated (Mechanical Ventilation): {intubated:4d} ({intubated / total_episodes * 100:5.1f}%)")
    print(f"  • Inotropic Support (Vasopressors):    {inotropes:4d} ({inotropes / total_episodes * 100:5.1f}%)")
    print(f"  • Central Venous Line (CVL):          {cvl:4d} ({cvl / total_episodes * 100:5.1f}%)")
    print(f"  • Umbilical Arterial Line (UAL):       {ual:4d} ({ual / total_episodes * 100:5.1f}%)")

    # Time to Antibiotics & Clinical Outcomes
    print("\n" + "-" * 65)
    print("5. CLINICAL MANAGEMENT & OUTCOMES")
    print("-" * 65)
    tta = df["time_to_antibiotics"].dropna()
    print(f"Time to First Antibiotics (minutes): Median = {tta.median():.0f} min ({tta.median() / 60:.1f} hrs) | IQR = [{tta.quantile(0.25):.0f} - {tta.quantile(0.75):.0f}] min")
    
    m7 = df["overall_mortality_within_7_days"].sum()
    m14 = df["overall_mortality_within_14_days"].sum()
    m30 = df["overall_mortality_within_30_days"].sum()
    print(f"Mortality within 7 Days:   {m7:3d} ({m7 / total_episodes * 100:.1f}%)")
    print(f"Mortality within 14 Days:  {m14:3d} ({m14 / total_episodes * 100:.1f}%)")
    print(f"Mortality within 30 Days:  {m30:3d} ({m30 / total_episodes * 100:.1f}%)")
    print("=" * 65)


def export_summary(df, output_file="sepsis_analysis_report.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("NEOGUARDIAN - NEONATAL SEPSIS EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Evaluation Episodes: {len(df)}\n")
        f.write(f"Unique Neonates: {df['unique_patient_id'].nunique()}\n")
        f.write(f"Culture Positive Sepsis: {df['blood_culture_positive'].sum()}\n")
        f.write(f"30-Day Mortality: {df['overall_mortality_within_30_days'].sum()}\n")
    print(f"\nSummary successfully saved to {output_file}")


def main():
    df = load_dataset()
    analyze_cohort(df)
    export_summary(df)


if __name__ == "__main__":
    main()
