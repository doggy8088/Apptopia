export function formatPace(totalSeconds) {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    return null;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  return `${minutes}'${String(seconds).padStart(2, "0")}"`;
}

export function parsePaceInput(rawValue) {
  const raw = rawValue.trim();
  if (!raw) {
    throw new Error("請輸入配速數值");
  }

  if (/[^0-9:'"\s]/.test(raw)) {
    throw new Error("請輸入有效的配速格式");
  }

  let minutes;
  let seconds;

  const normalized = raw.replace(/[\s]/g, "");
  const hasSeparator = /[:']/.test(normalized) || normalized.includes("\"");

  if (hasSeparator) {
    const parts = normalized.replace(/["']/g, ":").split(":").filter(Boolean);
    if (parts.length > 2) {
      throw new Error("請輸入有效的配速格式");
    }
    minutes = Number.parseInt(parts[0], 10);
    seconds = Number.parseInt(parts[1] ?? "0", 10);
  } else {
    if (!/^\d+$/.test(normalized)) {
      throw new Error("請輸入有效的配速格式");
    }
    if (normalized.length <= 2) {
      minutes = Number.parseInt(normalized, 10);
      seconds = 0;
    } else {
      minutes = Number.parseInt(normalized.slice(0, -2), 10);
      seconds = Number.parseInt(normalized.slice(-2), 10);
    }
  }

  if (!Number.isFinite(minutes) || !Number.isFinite(seconds)) {
    throw new Error("請輸入有效的配速格式");
  }

  const totalSeconds = minutes * 60 + seconds;
  if (totalSeconds <= 0) {
    throw new Error("配速必須大於 0");
  }

  return normalizePace(totalSeconds);
}

export function normalizePace(totalSeconds) {
  const total = Math.round(totalSeconds);
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return { minutes, seconds, totalSeconds: total };
}

export function speedToPace(speed) {
  if (!Number.isFinite(speed) || speed <= 0) {
    throw new Error("時速必須大於 0");
  }
  const totalSeconds = Number((3600 / speed).toFixed(1));
  return normalizePace(totalSeconds);
}

export function paceToSpeed(totalSeconds) {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    throw new Error("配速必須大於 0");
  }
  return Number((3600 / totalSeconds).toFixed(1));
}

export function formatPaceInput({ minutes, seconds }) {
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
