-- Healthcare Readmission MVP — PostgreSQL schema
-- Tables match Week 2 assignment: patient_encounters + care_interventions

DROP TABLE IF EXISTS care_interventions;
DROP TABLE IF EXISTS patient_encounters;

CREATE TABLE patient_encounters (
    encounter_id              BIGINT PRIMARY KEY,
    patient_nbr               BIGINT NOT NULL,
    age                       VARCHAR(20) NOT NULL,
    time_in_hospital          INTEGER NOT NULL,
    number_inpatient          INTEGER NOT NULL DEFAULT 0,
    number_emergency          INTEGER NOT NULL DEFAULT 0,
    number_outpatient         INTEGER NOT NULL DEFAULT 0,
    num_medications           INTEGER NOT NULL DEFAULT 0,
    num_lab_procedures        INTEGER NOT NULL DEFAULT 0,
    discharge_disposition_id  INTEGER NOT NULL,
    admission_type_id         INTEGER NOT NULL,
    -- Historical outcome only — do NOT use when calculating risk_score
    readmitted                VARCHAR(10) NOT NULL,
    -- Filled by the application after scoring (service layer)
    risk_score                INTEGER,
    risk_level                VARCHAR(10),

    CONSTRAINT chk_readmitted
        CHECK (readmitted IN ('NO', '<30', '>30')),
    CONSTRAINT chk_risk_level
        CHECK (risk_level IS NULL OR risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT chk_risk_score
        CHECK (risk_score IS NULL OR risk_score >= 0)
);

CREATE TABLE care_interventions (
    intervention_id  BIGSERIAL PRIMARY KEY,
    encounter_id     BIGINT NOT NULL UNIQUE
                     REFERENCES patient_encounters (encounter_id)
                     ON DELETE CASCADE,
    status           VARCHAR(40) NOT NULL DEFAULT 'PENDING_REVIEW',
    assigned_to      TEXT,
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_intervention_status
        CHECK (status IN (
            'PENDING_REVIEW',
            'ASSIGNED',
            'CONTACTED',
            'FOLLOW_UP_SCHEDULED',
            'CLOSED'
        ))
);

-- Helpful for care-queue and operations queries
CREATE INDEX idx_patient_encounters_risk_level
    ON patient_encounters (risk_level);

CREATE INDEX idx_patient_encounters_patient_nbr
    ON patient_encounters (patient_nbr);

CREATE INDEX idx_care_interventions_status
    ON care_interventions (status);
