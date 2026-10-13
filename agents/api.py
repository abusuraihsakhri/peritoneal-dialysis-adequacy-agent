"""
FastAPI REST API Server for Peritoneal Dialysis Adequacy Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from peritoneal_dialysis_adequacy_agent.clinical import pet_creatinine, weekly_ktv
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Peritoneal Dialysis Adequacy Agent API",
    description="Enterprise Distributed Component Platform (Nephrology & Dialysis Systems)",
    version="3.0.0-ENTERPRISE",
)


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
    return {"status": "HEALTHY", "service": "peritoneal-dialysis-adequacy-agent", "domain": "Nephrology & Dialysis Systems", "standard": "KDIGO / KDOQI Clinical Practice Guidelines", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "LEGACY_DEMONSTRATION"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


@app.post("/api/pet")
def api_pet(req: PETRequest):
    """Educational standardized 4-hour PET measurement."""
    try:
        return pet_creatinine(req.dialysate_creatinine_4h, req.plasma_creatinine)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/ktv")
def api_ktv(req: KtVRequest):
    """Educational 24-hour collection-based weekly Kt/V calculation."""
    try:
        return weekly_ktv(
            req.serum_urea, req.dialysate_urea, req.daily_drain_volume_l,
            req.urea_distribution_volume_l, req.urine_urea, req.daily_urine_volume_l,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
