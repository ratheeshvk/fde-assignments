export interface InterventionInput {
    status: string;
    assigned_to: string;
    notes: string;
}

export interface InterventionOutput {
    intervention_id: number;
    encounter_id: number;
    status: string;
    assigned_to: string;
    notes: string | null;
    created_at: string;
    updated_at: string;
}