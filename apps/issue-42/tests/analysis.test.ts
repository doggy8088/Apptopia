import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";
import { analyzeText } from "../src/analysis";

const fixturePath = path.join(__dirname, "fixtures", "prd.md");

describe("analyzeText", () => {
  it("extracts specific summary and required capabilities", () => {
    const text = fs.readFileSync(fixturePath, "utf8");
    const now = new Date("2024-01-01T00:00:00.000Z");
    const analysis = analyzeText(text, [fixturePath], now);

    expect(analysis.summary).toContain("Build a CLI tool that analyzes PRD and spec documents");
    expect(analysis.projectType).toBe("cli tool");
    expect(analysis.createdAt).toBe("2024-01-01T00:00:00.000Z");

    const capabilityNames = analysis.requiredCapabilities.map((capability) => capability.name);
    expect(capabilityNames).toEqual(
      expect.arrayContaining([
        "requirement_analysis",
        "capability_mapping",
        "registry_comparison",
        "execution_planning"
      ])
    );
  });
});
