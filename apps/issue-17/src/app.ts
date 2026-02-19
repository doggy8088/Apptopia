import { promises as fs } from "node:fs";
import path from "node:path";
import { analyzeResources } from "./analyzer";
import { API_RULES, SUPPORTED_VERSION_RANGE } from "./rules";
import {
  createReport,
  renderHtmlReport,
  renderJsonReport,
  renderTextReport
} from "./report";
import { scanFromManifestPaths } from "./scanner";
import { CliOptions, ReporterIO } from "./types";
import { validateVersionPair } from "./version";

const DEFAULT_IO: ReporterIO = {
  stdout: (message: string) => {
    process.stdout.write(message);
  },
  stderr: (message: string) => {
    process.stderr.write(message);
  }
};

function renderByFormat(format: CliOptions["output"], report: ReturnType<typeof createReport>): string {
  if (format === "json") {
    return renderJsonReport(report);
  }

  if (format === "html") {
    return renderHtmlReport(report);
  }

  return renderTextReport(report);
}

export async function runWithOptions(options: CliOptions, io: ReporterIO = DEFAULT_IO): Promise<number> {
  const { current, target } = validateVersionPair(
    options.currentVersion,
    options.targetVersion,
    SUPPORTED_VERSION_RANGE
  );

  let mode: "manifest" | "cluster";

  const manifestPaths = options.manifestPaths.map((item) => item.trim()).filter(Boolean);

  if (manifestPaths.length > 0) {
    mode = "manifest";
  } else if (options.kubeconfig) {
    mode = "cluster";
    throw new Error(
      "Cluster scanning through --kubeconfig is planned but not implemented in this bootstrap version. Use --from-manifests for now."
    );
  } else {
    throw new Error("Either --from-manifests or --kubeconfig must be provided.");
  }

  const resources = await scanFromManifestPaths(manifestPaths, options.namespaces);
  const findings = analyzeResources(resources, target, API_RULES);

  const report = createReport({
    currentVersion: current.normalized,
    targetVersion: target.normalized,
    mode,
    findings,
    totalResources: resources.length
  });

  const rendered = renderByFormat(options.output, report);

  if (options.outputFile) {
    const outputPath = path.resolve(options.outputFile);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, rendered, "utf8");
    io.stdout(`Report written to ${outputPath}\n`);
  } else {
    io.stdout(`${rendered}\n`);
  }

  return report.summary.overall === "compatible" ? 0 : 1;
}
