import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";
import { analyzeText } from "../src/analysis";

const fixturePath = path.join(__dirname, "fixtures", "prd.md");

describe("analyzeText", () => {
  it("extracts summary and required capabilities", () => {
    const text = fs.readFileSync(fixturePath, "utf8");
    const analysis = analyzeText(text, [fixturePath]);

    expect(analysis.summary.length).toBeGreaterThan(10);
    expect(analysis.requiredCapabilities.length).toBeGreaterThan(0);
    expect(analysis.projectType).toBe("cli tool");
  });
});
