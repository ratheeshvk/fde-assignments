from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReadmittedOutcome = Literal["NO", "<30", ">30"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]

InterventionStatus = Literal[
    "PENDING_REVIEW",
    "ASSIGNED",
    "CONTACTED",
    "FOLLOW_UP_SCHEDULED",
    "CLOSED",
]


class Encounter(BaseModel):
    encounter_id: int
    patient_nbr: int
    age: str
    time_in_hospital: int
    number_inpatient: int
    number_emergency: int
    number_outpatient: int = 0
    num_medications: int
    num_lab_procedures: int = 0
    discharge_disposition_id: int = 1
    admission_type_id: int = 1
    readmitted: ReadmittedOutcome = "NO"
    risk_score: int | None = None
    risk_level: RiskLevel | None = None
    status: str = ""
    assigned_to: str = ""


class CareIntervention(BaseModel):
    intervention_id: int
    encounter_id: int
    status: InterventionStatus = "PENDING_REVIEW"
    assigned_to: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class InterventionUpdate(BaseModel):
    status: InterventionStatus | None = None
    assigned_to: str | None = Field(default=None, min_length=1)
    notes: str | None = None


class CareQueueItem(BaseModel):
    encounter_id: int
    patient_nbr: int
    age: str
    risk_score: int
    risk_level: RiskLevel
    peak_risk_score: int
    peak_risk_level: RiskLevel
    time_in_hospital: int
    number_inpatient: int
    number_emergency: int
    number_outpatient: int
    num_medications: int
    intervention_id: int | None = None
    status: InterventionStatus | None = None
    assigned_to: str | None = None
    notes: str | None = None


class OperationsSummary(BaseModel):
    total_encounters: int
    high_risk: int
    medium_risk: int
    low_risk: int
    pending_interventions: int
    completed_interventions: int


class ReadmissionAnalysis(BaseModel):
    high_risk_patients: int
    high_risk_readmitted_under_30_days: int
    high_risk_readmission_rate: float
    medium_risk_patients: int = 0
    medium_risk_readmitted_under_30_days: int = 0
    medium_risk_readmission_rate: float = 0.0
    low_risk_patients: int = 0
    low_risk_readmitted_under_30_days: int = 0
    low_risk_readmission_rate: float = 0.0


class ManagementDashboard(BaseModel):
    total_encounters: int
    high_risk: int
    medium_risk: int
    low_risk: int
    care_queue_size: int
    pending_review: int
    assigned: int
    contacted: int
    follow_up_scheduled: int
    closed: int
    high_risk_readmission_rate: float