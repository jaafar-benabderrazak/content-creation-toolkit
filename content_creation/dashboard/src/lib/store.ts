export interface StatusEntry {
  timestamp: string; // ISO 8601
  stage: string; // e.g. "suno", "sdxl", "remotion", "upload"
  message: string;
  level: "info" | "warning" | "error";
}

const MAX_ENTRIES = 50;
const log: StatusEntry[] = [];

export function appendStatus(entry: StatusEntry): void {
  log.push(entry);
  if (log.length > MAX_ENTRIES) log.shift();
}

export function getStatusLog(): StatusEntry[] {
  return [...log];
}

export function clearStatusLog(): void {
  log.length = 0;
}
