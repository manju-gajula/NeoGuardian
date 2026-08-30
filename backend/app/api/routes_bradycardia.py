"""
Bradycardia API Router (Condition 2)
Computes continuous instantaneous heart rate from ECG R-peaks, identifies acute
bradycardia decelerations (< 100 BPM), and reports spells per hour from PICSDB data.
"""

from fastapi import APIRouter, HTTPException, Query
from app.schemas import BradycardiaResponse
from app.ml.bradycardia_detector import detect_bradycardia_for_infant
from app.data_loader import DataLoader

router = APIRouter(prefix="/api/bradycardia", tags=["Condition 2: Bradycardia"])


@router.get("/{infant_id}", response_model=BradycardiaResponse)
def get_bradycardia_diagnostics(
    infant_id: str,
    window_start_sec: float = Query(13080.0, description="Start timestamp in seconds (default ~218 min)"),
    window_duration_sec: float = Query(180.0, ge=30.0, le=600.0, description="Duration in seconds (30s to 600s)")
):
    loader = DataLoader.get_instance()
    clean_id = infant_id.lower()
    if clean_id.isdigit():
        clean_id = f"infant{clean_id}"

    # Verify that this record exists in PICSDB
    if clean_id not in loader.waveform_records and clean_id not in [f"infant{i}" for i in range(1, 11)]:
        raise HTTPException(
            status_code=404,
            detail=f"Infant ECG record '{infant_id}' not found. Valid PICSDB records are: {', '.join(loader.waveform_records)}."
        )

    try:
        result = detect_bradycardia_for_infant(
            infant_id=clean_id,
            window_start_sec=window_start_sec,
            window_duration_sec=window_duration_sec
        )
        return result
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing bradycardia trend: {str(e)}")
