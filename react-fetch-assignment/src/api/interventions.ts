import { API_BASE_URL } from "../config.ts";
import type { InterventionInput, InterventionOutput } from "../types/intervention.ts";

export async function assignIntervention(intervention_id: number, intervention: InterventionInput) {
    const response = await fetch(`${API_BASE_URL}/interventions/${intervention_id}`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(intervention),
    });
    const data: InterventionOutput = await response.json();
    return data;
}

const intervention: InterventionInput = {
    status: "ASSIGNED",
    assigned_to: "Care Team A",
    notes: "Patient assigned for follow-up"
};

console.log(await assignIntervention(259899924, intervention));
