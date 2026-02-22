import { describe, expect, it } from "vitest";
import { MAX_DURATION_SECONDS, TELEGRAM_MAX_FILE_BYTES } from "../src/constants";
import { isDurationAllowed, isFileSizeAllowed } from "../src/limits";

describe("limits", () => {
  it("allows duration within limit", () => {
    expect(isDurationAllowed(MAX_DURATION_SECONDS)).toBe(true);
    expect(isDurationAllowed(MAX_DURATION_SECONDS + 1)).toBe(false);
  });

  it("allows size within limit", () => {
    expect(isFileSizeAllowed(TELEGRAM_MAX_FILE_BYTES)).toBe(true);
    expect(isFileSizeAllowed(TELEGRAM_MAX_FILE_BYTES + 1)).toBe(false);
  });
});
