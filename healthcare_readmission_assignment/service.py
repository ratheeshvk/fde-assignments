"""Business logic layer — risk rules and workflow orchestration."""

from fastapi import HTTPException

import repository
from models import (
    CareQueueItem,
    Encounter,
    InterventionUpdate,
    ManagementDashboard,
    OperationsSummary,
    ReadmissionAnalysis,
    RiskLevel,
)

QUEUED_RISK_LEVELS = ["MEDIUM", "HIGH"]

EXPIRED_DISPOSITIONS = [11, 19, 20, 21]
HOSPICE_DISPOSITIONS = [13, 14]


def calculate_risk_score(encounter: Encounter) -> int:
    score = 0
    if encounter.number_inpatient >= 3:
        score += 3
    if encounter.number_emergency >= 2:
        score += 2
    if encounter.number_outpatient >= 3:
        score += 1
    if encounter.time_in_hospital >= 7:
        score += 1
    if encounter.num_medications >= 20:
        score += 1
    return score


def risk_level_from_score(score: int) -> RiskLevel:
    if score >= 5:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def list_encounters(limit: int | None = None, offset: int = 0) -> list[Encounter]:
    rows = repository.get_all_encounters(limit, offset)
    return [Encounter(**row) for row in rows]


def get_encounter(encounter_id: int) -> Encounter:
    row = repository.get_encounter_by_id(encounter_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return Encounter(**row)


def score_all_encounters() -> dict:
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    updates: list[tuple[int, int, str]] = []

    for encounter in list_encounters():
        score = calculate_risk_score(encounter)
        level = risk_level_from_score(score)
        updates.append((encounter.encounter_id, score, level))
        counts[level] += 1

    repository.bulk_update_risks(updates)
    return {**counts, "total": len(updates)}


def seed_care_queue() -> dict:
    """
    One intervention per patient who ever scored MEDIUM or HIGH, on their latest
    encounter. Patients who died on any encounter, or whose latest discharge was
    to hospice, are not queued.
    """
    rule = (
        QUEUED_RISK_LEVELS,
        EXPIRED_DISPOSITIONS + HOSPICE_DISPOSITIONS,
        EXPIRED_DISPOSITIONS,
    )
    removed = repository.delete_stale_pending_interventions(*rule)
    created = repository.create_pending_interventions(*rule)
    return {"interventions_created": created, "stale_interventions_removed": removed}


def run_scoring_pipeline() -> dict:
    score_counts = score_all_encounters()
    return {**score_counts, **seed_care_queue()}


def get_care_queue() -> list[CareQueueItem]:
    rows = repository.get_care_queue(QUEUED_RISK_LEVELS)
    return [CareQueueItem(**row) for row in rows]


def get_high_care_queue() -> list[CareQueueItem]:
    rows = repository.get_care_queue(["HIGH"])
    return [CareQueueItem(**row) for row in rows]


def update_intervention(encounter_id: int, payload: InterventionUpdate) -> dict:
    get_encounter(encounter_id)

    updated = repository.update_intervention(
        encounter_id,
        payload.status,
        payload.assigned_to,
        payload.notes,
    )
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Intervention not found for this encounter",
        )
    return updated


def get_operations_summary() -> OperationsSummary:
    return OperationsSummary(**repository.get_operations_summary())


def get_readmission_analysis() -> ReadmissionAnalysis:
    return ReadmissionAnalysis(**repository.get_readmission_analysis())


def get_management_dashboard() -> ManagementDashboard:
    return ManagementDashboard(**repository.get_management_dashboard())


if __name__ == "__main__":
    print(run_scoring_pipeline())
