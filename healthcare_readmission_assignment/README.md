# Diabetes Readmission Intervention Queue

## Business problem

A hospital has historical diabetes encounter data and is concerned about patients returning within 30 days of discharge.
The care-management team cannot manually review every discharged patient.

**Primary Business Decision:** Who needs to be contacted, so readmission can be avoided ?

## Users

- Care Management team
- Operational Team
- Clinical Leadership
- Finops

### What data set provides
- 101,766 historical inpatient encounters
- csv file with hospital records including hospital and medicine activity
- re-admitted status

### Dataset doesnt Include
- Preventable readmissions
- Cost of re admission
- Current hospital processes

## Architecture

| File | Responsibility |
|---|---|
| `database.py` | Reads `CONNECTION_STRING` from `.env` and opens connections |
| `data_loader.py` | Load CSV data in to `patient_encounters` |
| `repository.py` | CRUD operations on postgres database |
| `service.py` | Entire application logic, error handling |
| `models.py` | Request and response models |
| `main.py` | FastAPI app and endpoint definitions |
| `schema.sql` | Postgres Table creation statements |


## Intervention status flow:

```
PENDING_REVIEW → ASSIGNED → CONTACTED → FOLLOW_UP_SCHEDULED → CLOSED
```

## Risk scoring rule

Implemented in `service.calculate_risk_score`. It uses only utilization and stay attributes.

| Condition | Points |
|---|---|
| `number_inpatient >= 3` | +3 |
| `number_emergency >= 2` | +2 |
| `number_outpatient >= 3` | +1 |
| `time_in_hospital >= 7` | +1 |
| `num_medications >= 20` | +1 |

| Score | Risk level |
|---|---|
| 0–2 | LOW |
| 3–4 | MEDIUM |
| 5+ | HIGH |

**Data leakage rule:** `readmitted` is never read by the scoring code. It is only used afterwards, in `/operations/readmission-analysis`, to check whether the rule found a higher-risk population.

Every encounter is scored, but the care queue holds **one intervention per patient** based on risk level High or Medium

**Deceased:** and **Hospice:** patients are excluded from care intervention ( Found the code from dataset mapping )

## API
- Swagger `http://127.0.0.1:8000/docs`
- GET /encounters
- GET /encounter/{id}
- GET /care-queue
- GET /care-queue/{status}
- PATCH /interventions/{encounter_id} with body {"status": "CLOSED", "notes": "Follow-up workflow completed"}
- GET /operations/summary
- GET /operations/readmission-analysis
- GET /management/dashboard

## How to run
### Prerequisites
- Python 3.11+
- PostgreSQL running locally (for example Postgres.app)

### Steps

```bash
cd healthcare_readmission_assignment

# 1. Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Database connection
cp .env.example .env
# edit .env and set CONNECTION_STRING, e.g.
# CONNECTION_STRING=postgresql://user:password@localhost:5432/fde

# 3. Create tables (drops and recreates them)
psql "$CONNECTION_STRING" -f schema.sql

# 4. Load the dataset (~101k rows)
python data_loader.py

# 5. Score every encounter and build the care queue
python service.py

# 6. Start the API
uvicorn main:app --reload
```

### Verify the load

```sql
SELECT COUNT(*) FROM patient_encounters; 
```