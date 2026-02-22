export function parseDurationToSeconds(input: string): number | null {
  const trimmed = input.trim();
  if (!trimmed) {
    return null;
  }
  const parts = trimmed.split(":").map((value) => Number(value));
  if (parts.some((value) => Number.isNaN(value))) {
    return null;
  }
  if (parts.length === 1) {
    return Math.max(0, Math.floor(parts[0]));
  }
  if (parts.length === 2) {
    const [minutes, seconds] = parts;
    return Math.max(0, Math.floor(minutes * 60 + seconds));
  }
  if (parts.length === 3) {
    const [hours, minutes, seconds] = parts;
    return Math.max(0, Math.floor(hours * 3600 + minutes * 60 + seconds));
  }
  return null;
}

export function formatDuration(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const secs = safeSeconds % 60;
  const pad = (value: number) => value.toString().padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${pad(minutes)}:${pad(secs)}`;
  }
  return `${minutes}:${pad(secs)}`;
}
