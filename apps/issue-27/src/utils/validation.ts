export type UrlValidationResult =
  | { ok: true; url: string }
  | { ok: false; reason: string };

const urlRegex = /(https?:\/\/\S+)/i;

export function extractUrl(input: string): string | null {
  const match = input.match(urlRegex);
  return match ? match[1] : null;
}

export function validateUrl(url: string, maxBytes: number): UrlValidationResult {
  const length = Buffer.byteLength(url, 'utf8');
  if (length > maxBytes) {
    return { ok: false, reason: `URL 長度超過限制（${length} > ${maxBytes} bytes）。` };
  }

  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return { ok: false, reason: '只接受 http 或 https 連結。' };
    }
  } catch {
    return { ok: false, reason: 'URL 格式不正確。' };
  }

  return { ok: true, url };
}
