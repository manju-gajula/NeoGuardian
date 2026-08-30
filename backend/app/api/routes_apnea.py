"""
Apnea API Router (Condition 1)
Extracts downsampled respiration waveform signals, segments apnea pause events,
and evaluates respiratory instability rate from PICSDB plethysmography data.
"""

from fastapi import APIRouter, HTTPException, Query
from app.schemas import ApneaResponse
from app.ml.apnea_detector import detect_apnea_for_infant
from app.data_loader import DataLoader

router = APIRouter(prefix="/api/apnea", tags=["Condition 1: Apnea"])


@router.get("/{infant_id}", response_model=ApneaResponse)
def get_apnea_diagnostics(
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
            detail=f"Infant waveform record '{infant_id}' not found. Valid PICSDB records are: {', '.join(loader.waveform_records)}."
        )

    try:
        result = detect_apnea_for_infant(
            infant_id=clean_id,
            window_start_sec=window_start_sec,
            window_duration_sec=window_duration_sec
        )
        return result
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing apnea waveform: {str(e)}")
