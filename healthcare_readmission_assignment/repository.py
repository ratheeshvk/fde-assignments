"""Data access layer — SQL queries live here."""

from psycopg import sql
from psycopg.rows import dict_row

from database import get_connection
from models import Encounter

ENCOUNTER_INSERT_COLUMNS = (
    "encounter_id",
    "patient_nbr",
    "age",
    "time_in_hospital",
    "number_inpatient",
    "number_emergency",
    "number_outpatient",
    "num_medications",
    "num_lab_procedures",
    "discharge_disposition_id",
    "admission_type_id",
    "readmitted",
)

# Highest risk score / level a patient reached across all their encounters.
PATIENT_PEAK_RISK = """
    SELECT DISTINCT ON (patient_nbr)
        patient_nbr,
        risk_score AS peak_risk_score,
        risk_level AS peak_risk_level
    FROM patient_encounters
    ORDER BY patient_nbr, risk_score DESC
"""

# Each patient's most recent encounter with their peak risk level. The dataset
# has no dates, so the highest encounter_id is treated as the latest stay.
QUEUE_CANDIDATES = f"""
    SELECT DISTINCT ON (pe.patient_nbr)
        pe.encounter_id,
        pe.patient_nbr,
        pe.discharge_disposition_id,
        peak.peak_risk_level
    FROM patient_encounters pe
    JOIN ({PATIENT_PEAK_RISK}) peak ON peak.patient_nbr = pe.patient_nbr
    ORDER BY pe.patient_nbr, pe.encounter_id DESC
"""

# Encounters that should hold an intervention. Uses named parameters:
# risk_levels, latest_excluded_dispositions, any_excluded_dispositions.
QUEUE_ELIGIBLE = f"""
    SELECT candidates.encounter_id
    FROM ({QUEUE_CANDIDATES}) candidates
    WHERE candidates.peak_risk_level = ANY(%(risk_levels)s)
      AND candidates.discharge_disposition_id <> ALL(%(latest_excluded_dispositions)s)
      AND NOT EXISTS (
          SELECT 1 FROM patient_encounters x
          WHERE x.patient_nbr = candidates.patient_nbr
            AND x.discharge_disposition_id = ANY(%(any_excluded_dispositions)s)
      )
"""

CARE_QUEUE_SELECT = f"""
    SELECT
        pe.encounter_id,
        pe.patient_nbr,
        pe.age,
        pe.risk_score,
        pe.risk_level,
        peak.peak_risk_score,
        peak.peak_risk_level,
        pe.time_in_hospital,
        pe.number_inpatient,
        pe.number_emergency,
        pe.number_outpatient,
        pe.num_medications,
        ci.intervention_id,
        ci.status,
        ci.assigned_to,
        ci.notes
    FROM care_interventions ci
    JOIN patient_encounters pe ON pe.encounter_id = ci.encounter_id
    JOIN ({PATIENT_PEAK_RISK}) peak ON peak.patient_nbr = pe.patient_nbr
    WHERE peak.peak_risk_level = ANY(%s)
    ORDER BY peak.peak_risk_score DESC, pe.risk_score DESC, pe.encounter_id
"""


def clear_encounter_tables() -> None:
    """Remove loaded data so re-runs of the loader are repeatable."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE care_interventions, patient_encounters "
                "RESTART IDENTITY CASCADE"
            )
        conn.commit()


def bulk_insert_encounters(rows: list[tuple]) -> int:
    """Bulk-insert encounter tuples into patient_encounters via COPY."""
    if not rows:
        return 0

    columns = ", ".join(ENCOUNTER_INSERT_COLUMNS)
    copy_sql = f"COPY patient_encounters ({columns}) FROM STDIN"

    with get_connection() as conn:
        with conn.cursor() as cur:
            with cur.copy(copy_sql) as copy:
                for row in rows:
                    copy.write_row(row)
        conn.commit()
    return len(rows)


def get_all_encounters(limit: int | None = None, offset: int = 0) -> list[dict]:
    """limit=None returns every row (used by scoring)."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM patient_encounters "
                "ORDER BY encounter_id LIMIT %s OFFSET %s",
                (limit, offset),
            )
            return cursor.fetchall()


def get_encounter_by_id(encounter_id: int) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM patient_encounters WHERE encounter_id = %s",
                (encounter_id,),
            )
            return cursor.fetchone()

def search_encounters(
    patientNbr: int | None,
    riskLevel: str | None,
    riskScore: int | None,
) -> list[dict]:
    conditions: list[sql.Composable] = []
    parameters: list[int | str] = []

    if patientNbr is not None:
        conditions.append(sql.SQL("pe.patient_nbr = %s"))
        parameters.append(patientNbr)
    if riskLevel:
        conditions.append(sql.SQL("pe.risk_level = %s"))
        parameters.append(riskLevel)
    if riskScore is not None:
        conditions.append(sql.SQL("pe.risk_score = %s"))
        parameters.append(riskScore)

    where_clause = (
        sql.SQL("WHERE {}").format(sql.SQL(" AND ").join(conditions))
        if conditions
        else sql.SQL("")
    )
    query = sql.SQL(
        """
        SELECT
            pe.*,
            COALESCE(ci.status, '') AS status,
            COALESCE(ci.assigned_to, '') AS assigned_to
        FROM patient_encounters pe
        LEFT JOIN care_interventions ci
            ON ci.encounter_id = pe.encounter_id
        {where_clause}
        ORDER BY
            CASE ci.status
                WHEN 'PENDING_REVIEW' THEN 1
                WHEN 'ASSIGNED' THEN 2
                WHEN 'CONTACTED' THEN 3
                WHEN 'FOLLOW_UP_SCHEDULED' THEN 4
                WHEN 'CLOSED' THEN 5
                ELSE 6
            END,
            CASE pe.risk_level
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            pe.encounter_id
        """
    ).format(where_clause=where_clause)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                parameters,
            )
            return cursor.fetchall()

def add_encounter(encounter: Encounter) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO patient_encounters (
                    encounter_id, patient_nbr, age, time_in_hospital,
                    number_inpatient, number_emergency, number_outpatient,
                    num_medications, num_lab_procedures,
                    discharge_disposition_id, admission_type_id, readmitted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    encounter.encounter_id,
                    encounter.patient_nbr,
                    encounter.age,
                    encounter.time_in_hospital,
                    encounter.number_inpatient,
                    encounter.number_emergency,
                    encounter.number_outpatient,
                    encounter.num_medications,
                    encounter.num_lab_procedures,
                    encounter.discharge_disposition_id,
                    encounter.admission_type_id,
                    encounter.readmitted,
                ),
            )
        conn.commit()
def bulk_update_risks(updates: list[tuple[int, int, str]]) -> int:
    """
    Batch-update risk fields.
    Each tuple is (encounter_id, risk_score, risk_level).
    """
    if not updates:
        return 0
    payload = [(score, level, encounter_id) for encounter_id, score, level in updates]
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                UPDATE patient_encounters
                SET risk_score = %s, risk_level = %s
                WHERE encounter_id = %s
                """,
                payload,
            )
        conn.commit()
    return len(updates)


def create_pending_interventions(
    risk_levels: list[str],
    latest_excluded_dispositions: list[int],
    any_excluded_dispositions: list[int],
) -> int:
    """
    Queue each patient's latest encounter if any of their encounters reached one
    of the given risk levels, skipping excluded discharge dispositions.
    Existing interventions are left untouched.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO care_interventions (encounter_id, status)
                SELECT encounter_id, 'PENDING_REVIEW'
                FROM ({QUEUE_ELIGIBLE}) eligible
                ON CONFLICT (encounter_id) DO NOTHING
                """,
                {
                    "risk_levels": risk_levels,
                    "latest_excluded_dispositions": latest_excluded_dispositions,
                    "any_excluded_dispositions": any_excluded_dispositions,
                },
            )
            created = cursor.rowcount
        conn.commit()
    return created


def delete_stale_pending_interventions(
    risk_levels: list[str],
    latest_excluded_dispositions: list[int],
    any_excluded_dispositions: list[int],
) -> int:
    """
    Remove untouched PENDING_REVIEW interventions that no longer qualify for the
    queue. Interventions the care team has already worked on are kept.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM care_interventions
                WHERE status = 'PENDING_REVIEW'
                  AND assigned_to IS NULL
                  AND notes IS NULL
                  AND encounter_id NOT IN ({QUEUE_ELIGIBLE})
                """,
                {
                    "risk_levels": risk_levels,
                    "latest_excluded_dispositions": latest_excluded_dispositions,
                    "any_excluded_dispositions": any_excluded_dispositions,
                },
            )
            deleted = cursor.rowcount
        conn.commit()
    return deleted


def update_intervention(
    encounter_id: int,
    status: str | None,
    assigned_to: str | None,
    notes: str | None,
) -> dict | None:
    """Patch intervention fields by encounter_id. Only non-None fields are updated."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                UPDATE care_interventions
                SET
                    status = COALESCE(%s, status),
                    assigned_to = COALESCE(%s, assigned_to),
                    notes = COALESCE(%s, notes),
                    updated_at = NOW()
                WHERE encounter_id = %s
                RETURNING *
                """,
                (status, assigned_to, notes, encounter_id),
            )
            row = cursor.fetchone()
        conn.commit()
    return row


def get_care_queue(risk_levels: list[str]) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(CARE_QUEUE_SELECT, (risk_levels,))
            return cursor.fetchall()


def get_operations_summary() -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_encounters,
                    COUNT(*) FILTER (WHERE risk_level = 'HIGH') AS high_risk,
                    COUNT(*) FILTER (WHERE risk_level = 'MEDIUM') AS medium_risk,
                    COUNT(*) FILTER (WHERE risk_level = 'LOW') AS low_risk,
                    (
                        SELECT COUNT(*) FROM care_interventions
                        WHERE status = 'PENDING_REVIEW'
                    ) AS pending_interventions,
                    (
                        SELECT COUNT(*) FROM care_interventions
                        WHERE status = 'CLOSED'
                    ) AS completed_interventions
                FROM patient_encounters
                """
            )
            return cursor.fetchone()


def get_readmission_analysis() -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE risk_level = 'HIGH') AS high_risk_patients,
                    COUNT(*) FILTER (
                        WHERE risk_level = 'HIGH' AND readmitted = '<30'
                    ) AS high_risk_readmitted_under_30_days,
                    COALESCE(ROUND(
                        100.0 * COUNT(*) FILTER (
                            WHERE risk_level = 'HIGH' AND readmitted = '<30'
                        )
                        / NULLIF(COUNT(*) FILTER (WHERE risk_level = 'HIGH'), 0),
                        2
                    ), 0) AS high_risk_readmission_rate,
                    COUNT(*) FILTER (WHERE risk_level = 'MEDIUM') AS medium_risk_patients,
                    COUNT(*) FILTER (
                        WHERE risk_level = 'MEDIUM' AND readmitted = '<30'
                    ) AS medium_risk_readmitted_under_30_days,
                    COALESCE(ROUND(
                        100.0 * COUNT(*) FILTER (
                            WHERE risk_level = 'MEDIUM' AND readmitted = '<30'
                        )
                        / NULLIF(COUNT(*) FILTER (WHERE risk_level = 'MEDIUM'), 0),
                        2
                    ), 0) AS medium_risk_readmission_rate,
                    COUNT(*) FILTER (WHERE risk_level = 'LOW') AS low_risk_patients,
                    COUNT(*) FILTER (
                        WHERE risk_level = 'LOW' AND readmitted = '<30'
                    ) AS low_risk_readmitted_under_30_days,
                    COALESCE(ROUND(
                        100.0 * COUNT(*) FILTER (
                            WHERE risk_level = 'LOW' AND readmitted = '<30'
                        )
                        / NULLIF(COUNT(*) FILTER (WHERE risk_level = 'LOW'), 0),
                        2
                    ), 0) AS low_risk_readmission_rate
                FROM patient_encounters
                """
            )
            return cursor.fetchone()


def get_management_dashboard() -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM patient_encounters) AS total_encounters,
                    (SELECT COUNT(*) FROM patient_encounters WHERE risk_level = 'HIGH') AS high_risk,
                    (SELECT COUNT(*) FROM patient_encounters WHERE risk_level = 'MEDIUM') AS medium_risk,
                    (SELECT COUNT(*) FROM patient_encounters WHERE risk_level = 'LOW') AS low_risk,
                    (SELECT COUNT(*) FROM care_interventions) AS care_queue_size,
                    (SELECT COUNT(*) FROM care_interventions WHERE status = 'PENDING_REVIEW') AS pending_review,
                    (SELECT COUNT(*) FROM care_interventions WHERE status = 'ASSIGNED') AS assigned,
                    (SELECT COUNT(*) FROM care_interventions WHERE status = 'CONTACTED') AS contacted,
                    (
                        SELECT COUNT(*) FROM care_interventions
                        WHERE status = 'FOLLOW_UP_SCHEDULED'
                    ) AS follow_up_scheduled,
                    (SELECT COUNT(*) FROM care_interventions WHERE status = 'CLOSED') AS closed,
                    COALESCE(ROUND(
                        100.0 * (
                            SELECT COUNT(*) FROM patient_encounters
                            WHERE risk_level = 'HIGH' AND readmitted = '<30'
                        )
                        / NULLIF(
                            (SELECT COUNT(*) FROM patient_encounters WHERE risk_level = 'HIGH'),
                            0
                        ),
                        2
                    ), 0) AS high_risk_readmission_rate
                """
            )
            return cursor.fetchone()


def insert_encounter(encounter: Encounter) -> None:
    """Insert one encounter row."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO patient_encounters (
                    encounter_id, patient_nbr, age, time_in_hospital,
                    number_inpatient, number_emergency, number_outpatient,
                    num_medications, num_lab_procedures,
                    discharge_disposition_id, admission_type_id, readmitted,
                    risk_score, risk_level
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    encounter.encounter_id,
                    encounter.patient_nbr,
                    encounter.age,
                    encounter.time_in_hospital,
                    encounter.number_inpatient,
                    encounter.number_emergency,
                    encounter.number_outpatient,
                    encounter.num_medications,
                    encounter.num_lab_procedures,
                    encounter.discharge_disposition_id,
                    encounter.admission_type_id,
                    encounter.readmitted,
                    encounter.risk_score,
                    encounter.risk_level,
                ),
            )
        conn.commit()
