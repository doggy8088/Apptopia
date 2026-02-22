import { promises as dns } from "node:dns";
import net from "node:net";
import { MAX_URL_BYTES } from "../constants";

export interface UrlValidationResult {
  ok: boolean;
  url?: string;
  error?: string;
}

export interface UrlValidationOptions {
  skipDnsLookup?: boolean;
}

export function extractFirstUrl(text: string): string | null {
  const match = text.match(/https?:\/\/\S+/i);
  if (!match) {
    return null;
  }
  return match[0];
}

export async function validateUrlInput(
  value: string,
  options: UrlValidationOptions = {}
): Promise<UrlValidationResult> {
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
  const hostCheck = await validateHost(parsed.hostname, options);
  if (hostCheck) {
    return { ok: false, error: hostCheck };
  }
  return { ok: true, url: parsed.toString() };
}

async function validateHost(hostname: string, options: UrlValidationOptions): Promise<string | null> {
  const normalized = hostname.trim().toLowerCase();
  const host = normalized.startsWith("[") && normalized.endsWith("]")
    ? normalized.slice(1, -1)
    : normalized;
  if (!host) {
    return "網址缺少主機名稱。";
  }
  if (isBlockedHostname(host)) {
    return "不允許使用本機或內網網址。";
  }
  const ipVersion = net.isIP(host);
  if (ipVersion) {
    if (isPrivateIp(host)) {
      return "不允許使用本機或內網 IP。";
    }
    return null;
  }
  if (options.skipDnsLookup) {
    return null;
  }
  try {
    const addresses = await dns.lookup(host, { all: true, verbatim: true });
    if (addresses.length === 0) {
      return "網址無法解析。";
    }
    if (addresses.some((address) => isPrivateIp(address.address))) {
      return "不允許使用本機或內網網址。";
    }
  } catch {
    return "網址無法解析。";
  }
  return null;
}

function isBlockedHostname(hostname: string): boolean {
  if (hostname === "localhost" || hostname.endsWith(".localhost")) {
    return true;
  }
  if (hostname.endsWith(".local") || hostname.endsWith(".localdomain")) {
    return true;
  }
  if (hostname.endsWith(".internal") || hostname.endsWith(".lan")) {
    return true;
  }
  if (hostname.endsWith(".home") || hostname.endsWith(".home.arpa")) {
    return true;
  }
  return false;
}

function isPrivateIp(address: string): boolean {
  const version = net.isIP(address);
  if (version === 4) {
    return isPrivateIPv4(address);
  }
  if (version === 6) {
    return isPrivateIPv6(address);
  }
  return true;
}

function isPrivateIPv4(address: string): boolean {
  const parts = address.split(".").map((value) => Number.parseInt(value, 10));
  if (parts.length !== 4 || parts.some((value) => Number.isNaN(value))) {
    return true;
  }
  const [a, b, c] = parts;
  if (a === 0) return true;
  if (a === 10) return true;
  if (a === 127) return true;
  if (a === 100 && b >= 64 && b <= 127) return true;
  if (a === 169 && b === 254) return true;
  if (a === 172 && b >= 16 && b <= 31) return true;
  if (a === 192 && b === 168) return true;
  if (a === 192 && b === 0 && c === 0) return true;
  if (a === 192 && b === 0 && c === 2) return true;
  if (a === 198 && (b === 18 || b === 19)) return true;
  if (a === 198 && b === 51 && c === 100) return true;
  if (a === 203 && b === 0 && c === 113) return true;
  if (a >= 224) return true;
  return false;
}

function isPrivateIPv6(address: string): boolean {
  const normalized = address.split("%")[0]?.toLowerCase() ?? "";
  if (normalized === "::" || normalized === "::1") {
    return true;
  }
  if (normalized.startsWith("::ffff:")) {
    const ipv4 = normalized.slice("::ffff:".length);
    if (net.isIP(ipv4) === 4) {
      return isPrivateIPv4(ipv4);
    }
  }
  const hextets = parseIPv6(normalized);
  if (!hextets) {
    return true;
  }
  const first = hextets[0];
  if ((first & 0xffc0) === 0xfe80) return true;
  if ((first & 0xfe00) === 0xfc00) return true;
  if ((first & 0xff00) === 0xff00) return true;
  if (first === 0x2001 && hextets[1] === 0x0db8) return true;
  if ((first & 0xe000) !== 0x2000) return true;
  return false;
}

function parseIPv6(address: string): number[] | null {
  let working = address;
  if (working.includes(".")) {
    const lastColon = working.lastIndexOf(":");
    if (lastColon === -1) {
      return null;
    }
    const ipv4Part = working.slice(lastColon + 1);
    if (net.isIP(ipv4Part) !== 4) {
      return null;
    }
    const ipv4Numbers = ipv4Part.split(".").map((value) => Number.parseInt(value, 10));
    if (ipv4Numbers.some((value) => Number.isNaN(value))) {
      return null;
    }
    const first = (ipv4Numbers[0] << 8) | ipv4Numbers[1];
    const second = (ipv4Numbers[2] << 8) | ipv4Numbers[3];
    working = `${working.slice(0, lastColon)}:${first.toString(16)}:${second.toString(16)}`;
  }

  const parts = working.split("::");
  if (parts.length > 2) {
    return null;
  }
  const head = parts[0] ? parts[0].split(":").filter(Boolean) : [];
  const tail = parts[1] ? parts[1].split(":").filter(Boolean) : [];
  if (head.length + tail.length > 8) {
    return null;
  }
  const hextets: number[] = [];
  for (const part of head) {
    const value = Number.parseInt(part, 16);
    if (Number.isNaN(value)) {
      return null;
    }
    hextets.push(value);
  }
  const zerosToInsert = 8 - head.length - tail.length;
  for (let i = 0; i < zerosToInsert; i += 1) {
    hextets.push(0);
  }
  for (const part of tail) {
    const value = Number.parseInt(part, 16);
    if (Number.isNaN(value)) {
      return null;
    }
    hextets.push(value);
  }
  if (hextets.length !== 8) {
    return null;
  }
  return hextets;
}
