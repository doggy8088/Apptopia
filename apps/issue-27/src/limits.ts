import { MAX_DURATION_SECONDS, TELEGRAM_MAX_FILE_BYTES } from "./constants";

export function isDurationAllowed(durationSeconds: number): boolean {
  return durationSeconds <= MAX_DURATION_SECONDS;
}

export function isFileSizeAllowed(fileSizeBytes: number): boolean {
  return fileSizeBytes <= TELEGRAM_MAX_FILE_BYTES;
}
