"""
NeoGuardian Backend Application Server
FastAPI entrypoint orchestrating:
  - PICSDB continuous waveform processing (Apnea & Bradycardia)
  - Sepsis & Mortality ML inference with TreeSHAP feature attributions
  - Fused Neonatal Decompensation Index (NDI) early-warning alerts
  - Complete production React 18 SPA served directly at / and /assets
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.data_loader import DataLoader
from app.ml.sepsis_model import SepsisModelManager
from app.api.routes_patients import router as patients_router
from app.api.routes_apnea import router as apnea_router
from app.api.routes_bradycardia import router as bradycardia_router
from app.api.routes_sepsis import router as sepsis_router
from app.api.routes_ndi import router as ndi_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Preloads datasets and pre-trained ML models into memory once at startup
    so that all subsequent API endpoints respond with ultra-low latency.
    """
    print("=" * 65)
    print("  STARTING NEOGUARDIAN BACKEND APPLICATION SERVER")
    print("=" * 65)
    
    # 1. Preload datasets
    loader = DataLoader.get_instance()
    print(f"[Startup] Sepsis cohort ready: {len(loader.df_sepsis):,} episodes.")
    print(f"[Startup] PICSDB waveform records ready: {len(loader.waveform_records)} subjects.")

    # 2. Preload ML models and SHAP explainers
    model_mgr = SepsisModelManager.get_instance()
    models_ok = (model_mgr.sepsis_model is not None and model_mgr.mortality_model is not None)
    print(f"[Startup] Sepsis & Mortality ML models loaded: {models_ok}")

    # 3. Pre-warm waveform caches for the 10 monitored infants
    from app.ml.waveform_features import load_ecg_rpeaks, load_apnea_annotations
    for rec in loader.waveform_records[:10]:
        try:
            load_ecg_rpeaks(rec)
            load_apnea_annotations(rec)
        except Exception as e:
            print(f"[Startup] Note warming cache for {rec}: {e}")
    print(f"[Startup] Pre-warmed cardiorespiratory waveform caches.")

    print("=" * 65)
    print("  NEOGUARDIAN REST API IS READY FOR CLINICAL CLIENTS")
    print("=" * 65)
    yield
    print("[Shutdown] Shutting down NeoGuardian server.")


app = FastAPI(
    title="NeoGuardian API",
    description=(
        "AI-Based Intelligent Neonatal Health Monitoring & Early Warning System. "
        "Provides multi-condition detection and prediction for: "
        "1. Apnea of Prematurity (Respiration signal), "
        "2. Neonatal Bradycardia (ECG/HR signal), "
        "3. Late-Onset Sepsis & Mortality (Clinical features with TreeSHAP explainability), "
        "and fuses them into the composite Neonatal Decompensation Index (NDI)."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Condition-Specific & System Routers FIRST so API endpoints take priority
app.include_router(patients_router)
app.include_router(apnea_router)
app.include_router(bradycardia_router)
app.include_router(sepsis_router)
app.include_router(ndi_router)

# Mount static assets directory
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
assets_dir = os.path.join(static_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/dashboard", tags=["UI"])
def get_dashboard():
    """Direct shortcut for the clinical dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Dashboard index.html not found."}


@app.get("/", tags=["Root"])
def root(request: Request):
    """
    Root entrypoint:
    - In browser sessions: Serves the full compiled React 18 production UI.
    - In test/JSON clients: Returns system discovery metadata.
    """
    accept = request.headers.get("accept", "")
    user_agent = request.headers.get("user-agent", "").lower()
    index_file = os.path.join(static_dir, "index.html")

    # If accessed by a browser (HTML navigation), serve the React application
    if ("text/html" in accept or "mozilla" in user_agent) and os.path.exists(index_file):
        return FileResponse(index_file)

    # If called programmatically expecting JSON (e.g. pytest test_root or API probe)
    return {
        "system": "NeoGuardian",
        "title": "AI-Based Intelligent Neonatal Health Monitoring & Early Warning System",
        "status": "ONLINE",
        "docs_url": "/docs",
        "dashboard_url": "/dashboard",
        "api_endpoints": [
            "/api/health",
            "/api/patients",
            "/api/patients/{id}",
            "/api/apnea/{infant_id}",
            "/api/bradycardia/{infant_id}",
            "/api/predict/sepsis-risk",
            "/api/predict/mortality-risk",
            "/api/ndi/{patient_id}",
            "/api/alerts"
        ]
    }
