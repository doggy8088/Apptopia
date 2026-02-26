import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";
import { analyzeText } from "../src/analysis";
import { compareCapabilities } from "../src/compare";
import { generateDefinitions } from "../src/generate";

const fixturePath = path.join(__dirname, "fixtures", "prd.md");

describe("generateDefinitions", () => {
  it("generates definitions for missing capabilities", () => {
    const text = fs.readFileSync(fixturePath, "utf8");
    const analysis = analyzeText(text, [fixturePath]);
    const report = compareCapabilities(analysis.requiredCapabilities, null);
    const missing = analysis.requiredCapabilities.filter((capability) => {
      const coverage = report.coverage.find((item) => item.capability === capability.name);
      return coverage?.coverage === "unknown";
    });

    const generation = generateDefinitions(missing);
    expect(generation.classifications.length).toBeGreaterThan(0);
    expect(
      generation.skillDefinitions.length + generation.agentDefinitions.length
    ).toBeGreaterThan(0);
  });
});
