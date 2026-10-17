import { API_BASE_URL } from "../config.ts";
import type { Operations } from "../types/operations.ts";

export async function getOperations() {
    const response = await fetch(`${API_BASE_URL}/operations/summary`);
    const data: Operations = await response.json();
    return data;
}

console.log(await getOperations());