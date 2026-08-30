"""
Sepsis & Mortality Prediction API Router (Condition 3)
Provides ML inference endpoints with real TreeSHAP feature attributions for
estimating culture-confirmed sepsis risk and 30-day mortality probability.
"""

from fastapi import APIRouter
from app.schemas import (
    SepsisPredictionRequest,
    SepsisPredictionResponse,
    MortalityPredictionResponse
)
from app.ml.sepsis_model import SepsisModelManager

router = APIRouter(prefix="/api/predict", tags=["Condition 3: Sepsis"])


@router.post("/sepsis-risk", response_model=SepsisPredictionResponse)
def predict_sepsis_risk(request: SepsisPredictionRequest):
    manager = SepsisModelManager.get_instance()
    result = manager.predict_sepsis(request.model_dump())
    return result


@router.post("/mortality-risk", response_model=MortalityPredictionResponse)
def predict_mortality_risk(request: SepsisPredictionRequest):
    manager = SepsisModelManager.get_instance()
    result = manager.predict_mortality(request.model_dump())
    return result
