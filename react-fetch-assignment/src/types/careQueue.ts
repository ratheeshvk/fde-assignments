export interface CareQueue {
    encounter_id: number;
    patient_nbr: number;
    age: string;
    risk_score: number;
    risk_level: string;
    intervention_id: number;
    status: string;
    assigned_to: string;
    notes: string;
}
