"""
NeoGuardian Neonatal Decompensation Index (NDI) Fusion Engine
Combines three distinct neonatal conditions:
  1. Apnea Sub-Score (from respiration waveform stream)
  2. Bradycardia Sub-Score (from ECG heart rate stream)
  3. Sepsis Sub-Score (from ML clinical prediction & vitals)
  + Prematurity Vulnerability Score
Outputs a single unified early-warning score (0-100) with clinical bands:
  • 0-39: GREEN (Stable)
  • 40-64: YELLOW (Elevated Risk)
  • 65-100: RED (Critical Alert)
"""

from typing import Dict, Any, Tuple


def calculate_apnea_subscore(events_per_hour: float, max_duration_sec: float) -> float:
    score = 0.0
    if events_per_hour >= 4.0:
        score += 60.0
    elif events_per_hour >= 2.5:
        score += 40.0
    elif events_per_hour >= 1.0:
        score += 20.0
    else:
        score += 5.0

    if max_duration_sec >= 45.0:
        score += 40.0
    elif max_duration_sec >= 30.0:
        score += 25.0
    elif max_duration_sec >= 20.0:
        score += 15.0

    return min(100.0, score)


def calculate_bradycardia_subscore(lowest_hr_bpm: float, spells_per_hour: float) -> float:
    score = 0.0
    if lowest_hr_bpm < 70.0:
        score += 65.0
    elif lowest_hr_bpm < 85.0:
        score += 45.0
    elif lowest_hr_bpm < 100.0:
        score += 25.0
    elif lowest_hr_bpm < 115.0:
        score += 10.0

    if spells_per_hour >= 3.0:
        score += 35.0
    elif spells_per_hour >= 1.5:
        score += 20.0
    elif spells_per_hour >= 0.5:
        score += 10.0

    return min(100.0, score)


def calculate_sepsis_subscore(sepsis_prob: float, temp_celsius: float, has_cvl: bool) -> float:
    score = sepsis_prob * 65.0  # Up to 65 pts from ML model

    if temp_celsius < 36.5:
        score += 25.0  # Hypothermia penalty
    elif temp_celsius >= 38.0:
        score += 20.0  # Fever penalty

    if has_cvl:
        score += 10.0

    return min(100.0, score)


def calculate_vulnerability_score(ga_weeks: float, birth_weight_kg: float) -> float:
    score = 0.0
    if ga_weeks < 28.0:
        score += 55.0
    elif ga_weeks < 32.0:
        score += 35.0
    elif ga_weeks < 37.0:
        score += 15.0

    if birth_weight_kg < 1.0:
        score += 45.0
    elif birth_weight_kg < 1.5:
        score += 25.0

    return min(100.0, score)


def compute_fused_ndi(
    apnea_events_per_hour: float,
    apnea_max_duration_sec: float,
    lowest_hr_bpm: float,
    brady_spells_per_hour: float,
    sepsis_prob: float,
    temp_celsius: float,
    has_cvl: bool,
    ga_weeks: float,
    birth_weight_kg: float
) -> Dict[str, Any]:
    """
    Computes the composite NDI score and breaks it down into explicit sub-scores.
    """
    s_apnea = calculate_apnea_subscore(apnea_events_per_hour, apnea_max_duration_sec)
    s_brady = calculate_bradycardia_subscore(lowest_hr_bpm, brady_spells_per_hour)
    s_sepsis = calculate_sepsis_subscore(sepsis_prob, temp_celsius, has_cvl)
    s_vuln = calculate_vulnerability_score(ga_weeks, birth_weight_kg)

    # Weighted combination
    fused = (
        0.32 * s_apnea +
        0.32 * s_brady +
        0.26 * s_sepsis +
        0.10 * s_vuln
    )
    ndi_score = round(min(100.0, max(0.0, fused)), 1)

    # Band assignment
    if ndi_score >= 65.0:
        band = "RED"
        action = "CRITICAL ALERT: Immediate bedside physician review, blood gas, culture & empirical antibiotic protocol."
    elif ndi_score >= 40.0:
        band = "YELLOW"
        action = "ELEVATED RISK: Intensify cardiorespiratory monitor alarms and perform septic screening."
    else:
        band = "GREEN"
        action = "STABLE: Continue routine neonatal vital signs monitoring."

    # Identify primary driver
    scores = {
        "Apnea Instability": s_apnea,
        "Bradycardia Decelerations": s_brady,
        "Sepsis Risk / Thermal Instability": s_sepsis
    }
    primary_driver = max(scores, key=scores.get)

    rationale = (
        f"NDI is {ndi_score}/100 ({band}). Primary driver is {primary_driver}. "
        f"Sub-scores: Apnea={s_apnea:.0f}, Bradycardia={s_brady:.0f}, Sepsis={s_sepsis:.0f}."
    )

    return {
        "ndi_score": ndi_score,
        "ndi_band": band,
        "sub_scores": {
            "apnea_score": round(s_apnea, 1),
            "bradycardia_score": round(s_brady, 1),
            "sepsis_score": round(s_sepsis, 1),
            "prematurity_vulnerability_score": round(s_vuln, 1)
        },
        "primary_driver": primary_driver,
        "triage_action": action,
        "clinical_rationale": rationale
    }
