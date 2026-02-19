#!/usr/bin/env node
import { Command } from "commander";
import { runWithOptions } from "./app";
import { OutputFormat } from "./types";

function collectValues(value: string, previous: string[]): string[] {
  const values = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return [...previous, ...values];
}

async function main(): Promise<void> {
  const program = new Command();

  program
    .name("k8s-upgrade-validator")
    .description("Validate Kubernetes resource compatibility before cluster upgrade")
    .requiredOption("--current-version <version>", "Current Kubernetes version (example: 1.28)")
    .requiredOption("--target-version <version>", "Target Kubernetes version (example: 1.31)")
    .option("--kubeconfig <path>", "Kubeconfig path for cluster scanning mode")
    .option(
      "--from-manifests <path>",
      "Manifest file or directory path; repeat option or use comma-separated paths",
      collectValues,
      [] as string[]
    )
    .option(
      "--namespace <namespace>",
      "Limit namespaced resources; repeat option or use comma-separated values",
      collectValues,
      [] as string[]
    )
    .option("--output <format>", "Report format: text | json | html", "text")
    .option("--output-file <path>", "Write report to file path instead of stdout");

  program.parse(process.argv);
  const opts = program.opts<{
    currentVersion: string;
    targetVersion: string;
    kubeconfig?: string;
    fromManifests: string[];
    namespace: string[];
    output: string;
    outputFile?: string;
  }>();

  const output = opts.output as OutputFormat;
  if (!(["text", "json", "html"] as const).includes(output)) {
    throw new Error(`Invalid output format: ${opts.output}. Supported values: text, json, html.`);
  }

  const exitCode = await runWithOptions({
    currentVersion: opts.currentVersion,
    targetVersion: opts.targetVersion,
    kubeconfig: opts.kubeconfig,
    namespaces: opts.namespace ?? [],
    manifestPaths: opts.fromManifests ?? [],
    output,
    outputFile: opts.outputFile
  });

  process.exitCode = exitCode;
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`Error: ${message}\n`);
  process.exitCode = 2;
});
