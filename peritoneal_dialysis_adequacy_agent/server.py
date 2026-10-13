"""
FastAPI REST Application & Webhooks for PD-Sentinel: Peritoneal Equilibration Test (PET) & Transport Status Classifier.
"""
from typing import Dict, Any, Optional
from .models import ClinicalCasePayload
from .agents import PDCoordinator
from .clinical import pet_creatinine, weekly_ktv

coordinator = PDCoordinator()

def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="PD-Sentinel: Peritoneal Equilibration Test (PET) & Transport Status Classifier",
            description="Classifies peritoneal membrane transport (High, High-Average, Low-Average, Low) from 4h D/P creatinine and calculates weekly total Kt/V.",
            version="2.0.0-PRO",
        )

        class AuditRequest(BaseModel):
            case_id: str = "CASE-2026-001"
            patient_synthetic_id: str = "SYNTH-PT-881"
            primary_metric: float = 24.5
            secondary_metric: float = 14.0
            status_flag: str = "DISCORDANT"
            is_stat: bool = True
            clinical_notes: str = ""
            biomarkers: Dict[str, Any] = {}

        class PETRequest(BaseModel):
            dialysate_creatinine_4h: float = Field(..., allow_inf_nan=False, ge=0)
            plasma_creatinine: float = Field(..., allow_inf_nan=False, gt=0)

        class KtVRequest(BaseModel):
            serum_urea: float = Field(..., allow_inf_nan=False, gt=0)
            dialysate_urea: float = Field(..., allow_inf_nan=False, ge=0)
            daily_drain_volume_l: float = Field(..., allow_inf_nan=False, ge=0)
            urea_distribution_volume_l: float = Field(..., allow_inf_nan=False, gt=0)
            urine_urea: float | None = Field(default=None, allow_inf_nan=False, ge=0)
            daily_urine_volume_l: float | None = Field(default=None, allow_inf_nan=False, ge=0)

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "peritoneal-dialysis-adequacy-agent", "domain": "Nephrology", "version": "2.0.0-PRO"}

        @app.post("/api/audit")
        def api_audit(req: AuditRequest):
            payload = ClinicalCasePayload(
                case_id=req.case_id,
                patient_synthetic_id=req.patient_synthetic_id,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_flag=req.status_flag,
                is_stat=req.is_stat,
                clinical_notes=req.clinical_notes,
                biomarkers=req.biomarkers,
            )
            return coordinator.process_case(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        @app.post("/api/pet")
        def api_pet(req: PETRequest):
            try:
                return pet_creatinine(req.dialysate_creatinine_4h, req.plasma_creatinine)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.post("/api/ktv")
        def api_ktv(req: KtVRequest):
            try:
                return weekly_ktv(
                    req.serum_urea, req.dialysate_urea,
                    req.daily_drain_volume_l, req.urea_distribution_volume_l,
                    req.urine_urea, req.daily_urine_volume_l,
                )
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        return app
    except ImportError:
        return None
