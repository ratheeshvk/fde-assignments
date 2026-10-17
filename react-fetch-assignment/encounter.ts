export interface Encounter {

    encounter_id: number;
    patient_nbr: number;
    age: string;
    time_in_hospital: number;
    number_inpatient: number;
    number_emergency: number;
    number_outpatient: number;
    num_medications: number;
    num_lab_procedures: number;
}

export interface PatchEncounter {
    status: string;
    assigned_to: string;
    notes: string;
}