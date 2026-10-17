import type { Encounter } from "./encounter.ts";
import type { PatchEncounter } from "./encounter.ts";

async function getEncountersbyId(id: number ) {
    const response = await fetch(`http://localhost:8002/encounters/${id}`);
    const data: Encounter = await response.json();
    return data;
}

async function updateEncounter(encounter_id: number, patchEncounter: PatchEncounter) {
    const response = await fetch(`http://localhost:8002/encounters/${encounter_id}`, {
        method: "PATCH",
        body: JSON.stringify(patchEncounter),
    });
    const data: Encounter = await response.json();
    return data;
}

const data = await getEncountersbyId(40926);
console.log(data);

const patchEncounter: PatchEncounter = {
    "status": "ASSIGNED",
    "assigned_to": "Care Team A",
    "notes": "Patient assigned for follow-up"
}

const data2 = await updateEncounter(62256, patchEncounter);
console.log(data2);


const encounter1: Encounter = {
    "encounter_id": 12522,
    "patient_nbr": 48330783,
    "age": "[80-90)",
    "time_in_hospital": 13,
    "number_inpatient": 0,
    "number_emergency": 0,
    "number_outpatient": 0,
    "num_medications": 28,
    "num_lab_procedures": 68,
}

const encounter2: Encounter = {
    "encounter_id": 15738,
    "patient_nbr": 63555939,
    "age": "[90-100)",
    "time_in_hospital": 12,
    "number_inpatient": 0,
    "number_emergency": 0,
    "number_outpatient": 0,
    "num_medications": 18,
    "num_lab_procedures": 33
}

const encounters: Encounter[] = [encounter1, encounter2];

console.log(encounters);