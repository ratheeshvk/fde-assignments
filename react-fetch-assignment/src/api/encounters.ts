import { API_BASE_URL } from "../config.ts";
import type { Encounter } from "../types/encounter.ts";

export async function getEncountersById(encounter_id: number) {
    const response = await fetch(`${API_BASE_URL}/encounters/${encounter_id}`);
    const data: Encounter = await response.json();
    return data;
}

console.log(await getEncountersById(180911358));