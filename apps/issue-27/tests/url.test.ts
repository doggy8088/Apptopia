import { describe, expect, it } from "vitest";
import { extractFirstUrl, validateUrlInput } from "../src/utils/url";

describe("url utils", () => {
  it("extracts first url", () => {
    const text = "hello https://example.com/video and more";
    expect(extractFirstUrl(text)).toBe("https://example.com/video");
  });

  it("validates http url", () => {
    const result = validateUrlInput("https://example.com");
    expect(result.ok).toBe(true);
  });

  it("rejects invalid url", () => {
    const result = validateUrlInput("not-a-url");
    expect(result.ok).toBe(false);
  });

  it("rejects non-http url", () => {
    const result = validateUrlInput("ftp://example.com");
    expect(result.ok).toBe(false);
  });
});
