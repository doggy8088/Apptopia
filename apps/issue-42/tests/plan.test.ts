import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";
import { analyzeText } from "../src/analysis";
import { buildExecutionPlan } from "../src/plan";

const fixturePath = path.join(__dirname, "fixtures", "prd.md");

describe("buildExecutionPlan", () => {
  it("returns ordered steps", () => {
    const text = fs.readFileSync(fixturePath, "utf8");
    const analysis = analyzeText(text, [fixturePath], new Date("2024-01-01T00:00:00.000Z"));
    const plan = buildExecutionPlan(analysis);

    expect(plan.steps.length).toBeGreaterThan(0);
    expect(plan.dependencies.length).toBeGreaterThan(0);
  });
});
