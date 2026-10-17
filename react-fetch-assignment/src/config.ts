import path from "node:path";

process.loadEnvFile(path.join(import.meta.dirname, "../.env"));

export const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8002";
