import { describe, expect, it } from "vitest";
import { extractFirstUrl, validateUrlInput } from "../src/utils/url";

describe("url utils", () => {
  it("extracts first url", () => {
    const text = "hello https://example.com/video and more";
    expect(extractFirstUrl(text)).toBe("https://example.com/video");
  });

  it("validates http url", async () => {
    const result = await validateUrlInput("https://example.com", { skipDnsLookup: true });
    expect(result.ok).toBe(true);
  });

  it("rejects invalid url", async () => {
    const result = await validateUrlInput("not-a-url", { skipDnsLookup: true });
    expect(result.ok).toBe(false);
  });

  it("rejects non-http url", async () => {
    const result = await validateUrlInput("ftp://example.com", { skipDnsLookup: true });
    expect(result.ok).toBe(false);
  });

  it("rejects localhost", async () => {
    const result = await validateUrlInput("http://localhost:8080", { skipDnsLookup: true });
    expect(result.ok).toBe(false);
  });

  it("rejects private ip", async () => {
    const result = await validateUrlInput("http://127.0.0.1/video", { skipDnsLookup: true });
    expect(result.ok).toBe(false);
  });

  it("rejects loopback ipv6", async () => {
    const result = await validateUrlInput("http://[::1]/video", { skipDnsLookup: true });
    expect(result.ok).toBe(false);
  });
});
