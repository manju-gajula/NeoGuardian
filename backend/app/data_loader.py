"""
NeoGuardian Data Loader
Manages in-memory caching of the PICSDB cardiorespiratory dataset and the
NICU sepsis cohort for fast, low-latency API queries.
"""

import os
import glob
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any


class DataLoader:
    _instance: Optional["DataLoader"] = None

    def __init__(self):
        # Locate project root directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

        self.sepsis_path = os.path.join(self.project_root, "data", "sepsis", "neonatal_sepsis.csv")
        if not os.path.exists(self.sepsis_path):
            alt_path = os.path.join(self.project_root, "data", "sepsis", "deid-nicu-sepsis-tta.csv")
            if os.path.exists(alt_path):
                self.sepsis_path = alt_path

        self.picsdb_dir = os.path.join(self.project_root, "data", "picsdb")

        self.df_sepsis: Optional[pd.DataFrame] = None
        self.patient_index: Dict[str, Dict[str, Any]] = {}
        self.waveform_records: List[str] = []

        self.load_all()

    @classmethod
    def get_instance(cls) -> "DataLoader":
        if cls._instance is None:
            cls._instance = DataLoader()
        return cls._instance

    def load_all(self):
        self._load_sepsis_data()
        self._scan_waveform_records()
        self._build_patient_index()

    def _load_sepsis_data(self):
        if os.path.exists(self.sepsis_path):
            print(f"[DataLoader] Preloading sepsis cohort from {self.sepsis_path}...")
            self.df_sepsis = pd.read_csv(self.sepsis_path)
            print(f"[DataLoader] Loaded {len(self.df_sepsis):,} sepsis episodes.")
        else:
            print(f"[DataLoader] Warning: Sepsis data file not found at {self.sepsis_path}.")
            self.df_sepsis = pd.DataFrame()

    def _scan_waveform_records(self):
        if os.path.exists(self.picsdb_dir):
            hea_files = glob.glob(os.path.join(self.picsdb_dir, "*_resp.hea"))
            self.waveform_records = sorted([
                os.path.basename(f).replace("_resp.hea", "") for f in hea_files
            ])
            print(f"[DataLoader] Discovered {len(self.waveform_records)} PICSDB infant records: {self.waveform_records}")
        else:
            print(f"[DataLoader] Warning: PICSDB directory not found at {self.picsdb_dir}.")
            self.waveform_records = []

    def _build_patient_index(self):
        """
        Creates a unified patient registry.
        Maps the 10 real PICSDB infant waveforms to the first 10 patients in the cohort,
        and indexes the remaining patients from the clinical sepsis database.
        """
        self.patient_index.clear()

        # Map the 10 waveform subjects
        for i, rec in enumerate(self.waveform_records, start=1):
            pid = f"infant{i}"
            # Extract row from sepsis dataset if available, or generate clinical surrogate
            if self.df_sepsis is not None and not self.df_sepsis.empty and i <= len(self.df_sepsis):
                row = self.df_sepsis.iloc[i - 1].to_dict()
            else:
                row = {
                    "unique_patient_id": i,
                    "gestational_age_at_birth_weeks": 26.0 + (i % 8),
                    "birth_weight_kg": 0.75 + (i * 0.15),
                    "sex": i % 2,
                    "onset_age_in_days": 5.0 + i,
                    "temp_celsius": 37.1 if i % 3 != 0 else (36.2 if i % 2 == 0 else 38.6),
                    "intubated_at_time_of_sepsis_evaluation": 1 if i in (1, 4, 7, 8) else 0,
                    "central_venous_line": 1 if i in (1, 2, 4, 6, 8, 10) else 0,
                    "inotrope_at_time_of_sepsis_eval": 1 if i == 1 else 0,
                }

            self.patient_index[pid] = {
                "id": pid,
                "display_id": f"NICU-INF-{i:03d}",
                "patient_number": i,
                "infant_record_id": rec,
                "has_waveform": True,
                "clinical_data": row
            }

        # Index remaining patients from the clinical sepsis dataset (up to 50 for rapid UI browsing)
        if self.df_sepsis is not None and not self.df_sepsis.empty:
            for idx, row in self.df_sepsis.iloc[len(self.waveform_records):60].iterrows():
                p_num = int(row.get("unique_patient_id", idx + 1))
                pid = f"pt_{p_num}_{idx}"
                self.patient_index[pid] = {
                    "id": pid,
                    "display_id": f"NICU-PT-{p_num:03d}",
                    "patient_number": p_num,
                    "infant_record_id": None,
                    "has_waveform": False,
                    "clinical_data": row.to_dict()
                }

        print(f"[DataLoader] Patient registry initialized with {len(self.patient_index)} patients.")

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        # Allow lookup by exact key (e.g. 'infant1') or numerical string ('1')
        if patient_id in self.patient_index:
            return self.patient_index[patient_id]

        if patient_id.isdigit():
            alt_key = f"infant{patient_id}"
            if alt_key in self.patient_index:
                return self.patient_index[alt_key]

        # Search by patient_number or display_id
        for p in self.patient_index.values():
            if str(p["patient_number"]) == patient_id or p["display_id"].lower() == patient_id.lower():
                return p

        return None

    def list_patients(self) -> List[Dict[str, Any]]:
        return list(self.patient_index.values())
