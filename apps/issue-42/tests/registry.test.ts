import { describe, expect, it } from "vitest";
import { validateRegistry } from "../src/registry";

const invalidRegistry = { skills: [] } as any;

describe("validateRegistry", () => {
  it("rejects missing agents array", () => {
    const result = validateRegistry(invalidRegistry);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});
