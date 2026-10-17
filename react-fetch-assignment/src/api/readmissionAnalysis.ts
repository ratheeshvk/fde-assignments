import { API_BASE_URL } from "../config.ts";
import type { ReadmissionAnalysis } from "../types/readmissionAnalysis.ts";

export async function getReadmissionAnalysis() {
    const response = await fetch(`${API_BASE_URL}/operations/readmission-analysis`);
    const data: ReadmissionAnalysis = await response.json();
    return data;
}

console.log(await getReadmissionAnalysis());