import { API_BASE_URL } from "../config.ts";
import type { CareQueue } from "../types/careQueue.ts";

export async function getCareQueue() {
    const response = await fetch(`${API_BASE_URL}/care-queue`);
    const data: CareQueue[] = await response.json();
    return data;
}

console.log(await getCareQueue());

export async function getCareQueueByRisk(risk: string) {
    const response = await fetch(`${API_BASE_URL}/care-queue/${risk}`);
    const data: CareQueue = await response.json();
    return data;
}

console.log(await getCareQueueByRisk("high"));