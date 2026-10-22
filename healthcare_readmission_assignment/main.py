from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import service
from models import (
    CareIntervention,
    CareQueueItem,
    Encounter,
    InterventionUpdate,
    ManagementDashboard,
    OperationsSummary,
    ReadmissionAnalysis,
)

app = FastAPI(
    title="Diabetes Readmission Intervention Queue",
    description="Learning prototype — not for clinical decision-making.",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/encounters", response_model=list[Encounter])
def list_encounters(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    return service.list_encounters(limit, offset)

@app.post("/encounters", response_model=Encounter)
def add_encounter(encounter: Encounter):
    return service.add_encounter(encounter)

@app.get("/encounters/search", response_model=list[Encounter])
def search_encounters(
    patientNbr: int | None = None,
    riskLevel: str | None = None,
    riskScore: int | None = None,
):
    return service.search_encounters(patientNbr, riskLevel, riskScore)


@app.get("/encounters/{encounter_id}", response_model=Encounter)
def get_encounter(encounter_id: int):
    return service.get_encounter(encounter_id)


@app.get("/care-queue", response_model=list[CareQueueItem])
def get_care_queue():
    return service.get_care_queue()


@app.get("/care-queue/high", response_model=list[CareQueueItem])
def get_high_care_queue():
    return service.get_high_care_queue()


@app.patch("/interventions/{encounter_id}", response_model=CareIntervention)
def update_intervention(encounter_id: int, payload: InterventionUpdate):
    return service.update_intervention(encounter_id, payload)


@app.get("/operations/summary", response_model=OperationsSummary)
def get_operations_summary():
    return service.get_operations_summary()


@app.get("/operations/readmission-analysis", response_model=ReadmissionAnalysis)
def get_readmission_analysis():
    return service.get_readmission_analysis()


@app.get("/management/dashboard", response_model=ManagementDashboard)
def get_management_dashboard():
    return service.get_management_dashboard()
