import { API_BASE_URL } from "../config.ts";
import type { Management } from "../types/management.ts";

export async function getManagement() {
    const response = await fetch(`${API_BASE_URL}/management/dashboard`);
    const data: Management = await response.json();
    return data;
}

console.log(await getManagement());