import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";
import { analyzeText } from "../src/analysis";
import { compareCapabilities } from "../src/compare";
import { RegistryData } from "../src/types";

const fixturePath = path.join(__dirname, "fixtures", "prd.md");
const registryPath = path.join(__dirname, "fixtures", "registry.json");

describe("compareCapabilities", () => {
  it("marks coverage with registry", () => {
    const text = fs.readFileSync(fixturePath, "utf8");
    const analysis = analyzeText(text, [fixturePath], new Date("2024-01-01T00:00:00.000Z"));
    const registry = JSON.parse(fs.readFileSync(registryPath, "utf8")) as RegistryData;

    const report = compareCapabilities(analysis.requiredCapabilities, registry);
    const covered = report.coverage.find((item) => item.coverage === "covered");

    expect(report.registryLoaded).toBe(true);
    expect(covered).toBeDefined();
  });
});
