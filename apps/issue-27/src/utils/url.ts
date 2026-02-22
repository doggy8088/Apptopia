import { MAX_URL_BYTES } from "../constants";

export interface UrlValidationResult {
  ok: boolean;
  url?: string;
  error?: string;
}

export function extractFirstUrl(text: string): string | null {
  const match = text.match(/https?:\/\/\S+/i);
  if (!match) {
    return null;
  }
  return match[0];
}

export function validateUrlInput(value: string): UrlValidationResult {
  const trimmed = value.trim();
  if (!trimmed) {
    return { ok: false, error: "請提供影片網址。" };
  }
  if (Buffer.byteLength(trimmed, "utf8") > MAX_URL_BYTES) {
    return { ok: false, error: "網址長度超過限制 (1000 bytes)。" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, error: "網址格式不正確。" };
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return { ok: false, error: "僅支援 http/https 網址。" };
  }
  return { ok: true, url: parsed.toString() };
}
