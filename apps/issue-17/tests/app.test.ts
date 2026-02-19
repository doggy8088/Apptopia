import { readFile } from "node:fs/promises";
import path from "node:path";
import Ajv from "ajv";
import { describe, expect, it } from "vitest";
import { runWithOptions } from "../src/app";
import { ReporterIO } from "../src/types";

function createCapture(): {
  io: ReporterIO;
  getStdout: () => string;
  getStderr: () => string;
} {
  let stdout = "";
  let stderr = "";

  return {
    io: {
      stdout: (message: string) => {
        stdout += message;
      },
      stderr: (message: string) => {
        stderr += message;
      }
    },
    getStdout: () => stdout,
    getStderr: () => stderr
  };
}

describe("k8s-upgrade-validator", () => {
  it("flags policy/v1beta1 PodDisruptionBudget as breaking and suggests policy/v1", async () => {
    const capture = createCapture();
    const exitCode = await runWithOptions(
      {
        currentVersion: "1.28",
        targetVersion: "1.31",
        manifestPaths: [path.resolve("tests/fixtures/breaking/pdb.yaml")],
        namespaces: [],
        output: "json"
      },
      capture.io
    );

    expect(exitCode).toBe(1);

    const report = JSON.parse(capture.getStdout());
    expect(report.summary.breaking).toBe(1);
    expect(report.findings).toHaveLength(1);
    expect(report.findings[0].resource.kind).toBe("PodDisruptionBudget");
    expect(report.findings[0].rule.replacementApiVersion).toBe("policy/v1");
  });

  it("returns exit code 0 when all resources are compatible", async () => {
    const capture = createCapture();
    const exitCode = await runWithOptions(
      {
        currentVersion: "1.28",
        targetVersion: "1.31",
        manifestPaths: [path.resolve("tests/fixtures/compatible/deployment.yaml")],
        namespaces: [],
        output: "text"
      },
      capture.io
    );

    expect(exitCode).toBe(0);
    expect(capture.getStdout()).toContain("All resources are compatible with the target version.");
  });

  it("produces JSON output that conforms to report schema", async () => {
    const capture = createCapture();
    await runWithOptions(
      {
        currentVersion: "1.28",
        targetVersion: "1.31",
        manifestPaths: [path.resolve("tests/fixtures/breaking/pdb.yaml")],
        namespaces: [],
        output: "json"
      },
      capture.io
    );

    const report = JSON.parse(capture.getStdout());
    const schemaRaw = await readFile(path.resolve("docs/report.schema.json"), "utf8");
    const schema = JSON.parse(schemaRaw);
    const ajv = new Ajv({ allErrors: true, strict: false });
    const validate = ajv.compile(schema);

    expect(validate(report)).toBe(true);
  });

  it("fails fast for unsupported target version with supported range in message", async () => {
    const capture = createCapture();

    await expect(
      runWithOptions(
        {
          currentVersion: "1.28",
          targetVersion: "1.99",
          manifestPaths: [path.resolve("tests/fixtures/breaking/pdb.yaml")],
          namespaces: [],
          output: "text"
        },
        capture.io
      )
    ).rejects.toThrow("Supported Kubernetes versions: v1.25 ~ v1.34");

    expect(capture.getStderr()).toBe("");
  });
});
