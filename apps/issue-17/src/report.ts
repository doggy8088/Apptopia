import { Finding, UpgradeReport } from "./types";

const UPGRADE_STEPS = [
  "Backup etcd data before any control-plane change.",
  "Fix all breaking API usages found by this report.",
  "Upgrade Kubernetes control plane components.",
  "Upgrade worker nodes in batches (drain/upgrade/uncordon).",
  "Verify workloads, networking, and storage health checks.",
  "Run post-upgrade validation and monitor cluster events."
];

function escapeHtml(input: string): string {
  return input
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatFindingLine(index: number, finding: Finding): string {
  const namespace = finding.resource.namespace ?? "cluster-scope";
  const replacement = finding.rule.replacementApiVersion
    ? ` -> ${finding.rule.replacementApiVersion}`
    : "";
  const milestone = finding.severity === "breaking" ? finding.rule.removedIn : finding.rule.deprecatedIn;
  const milestoneLabel = milestone ? ` (v${milestone})` : "";

  return `  ${index}. [${finding.resource.kind}] ${finding.resource.name} (namespace: ${namespace})\n` +
    `     - ${finding.resource.apiVersion}${replacement}${milestoneLabel}\n` +
    `     - ${finding.message}`;
}

export function createReport(args: {
  currentVersion: string;
  targetVersion: string;
  mode: "manifest" | "cluster";
  findings: Finding[];
  totalResources: number;
}): UpgradeReport {
  const breaking = args.findings.filter((item) => item.severity === "breaking").length;
  const warning = args.findings.filter((item) => item.severity === "warning").length;
  const compatible = Math.max(args.totalResources - args.findings.length, 0);

  return {
    tool: {
      name: "k8s-upgrade-validator",
      version: "0.1.0",
      mode: args.mode
    },
    currentVersion: args.currentVersion,
    targetVersion: args.targetVersion,
    generatedAt: new Date().toISOString(),
    summary: {
      totalResources: args.totalResources,
      breaking,
      warning,
      compatible,
      overall: breaking === 0 && warning === 0 ? "compatible" : "action-required"
    },
    findings: args.findings,
    upgradeSteps: [...UPGRADE_STEPS]
  };
}

export function renderTextReport(report: UpgradeReport): string {
  const lines: string[] = [];
  const breakingFindings = report.findings.filter((item) => item.severity === "breaking");
  const warningFindings = report.findings.filter((item) => item.severity === "warning");

  lines.push("=== K8s Upgrade Validation Report ===");
  lines.push(`From: v${report.currentVersion} -> To: v${report.targetVersion}`);
  lines.push("");
  lines.push(`Scanned resources: ${report.summary.totalResources}`);
  lines.push(`Compatible resources: ${report.summary.compatible}`);
  lines.push("");

  lines.push(`BREAKING (${breakingFindings.length}):`);
  if (breakingFindings.length === 0) {
    lines.push("  - none");
  } else {
    lines.push(
      ...breakingFindings.map((finding, index) => formatFindingLine(index + 1, finding))
    );
  }
  lines.push("");

  lines.push(`WARNINGS (${warningFindings.length}):`);
  if (warningFindings.length === 0) {
    lines.push("  - none");
  } else {
    lines.push(...warningFindings.map((finding, index) => formatFindingLine(index + 1, finding)));
  }
  lines.push("");

  if (report.summary.overall === "compatible") {
    lines.push("All resources are compatible with the target version.");
  } else {
    lines.push("Action is required before upgrade. Review findings below.");
  }

  lines.push("");
  lines.push("=== Upgrade Steps ===");
  report.upgradeSteps.forEach((step, index) => {
    lines.push(`Step ${index + 1}: ${step}`);
  });

  return lines.join("\n");
}

export function renderJsonReport(report: UpgradeReport): string {
  return JSON.stringify(report, null, 2);
}

export function renderHtmlReport(report: UpgradeReport): string {
  const rows = report.findings
    .map((finding) => {
      const namespace = finding.resource.namespace ?? "cluster-scope";
      const replacement = finding.rule.replacementApiVersion ?? "-";
      return `<tr>
  <td>${escapeHtml(finding.severity.toUpperCase())}</td>
  <td>${escapeHtml(finding.resource.kind)}</td>
  <td>${escapeHtml(finding.resource.name)}</td>
  <td>${escapeHtml(namespace)}</td>
  <td>${escapeHtml(finding.resource.apiVersion)}</td>
  <td>${escapeHtml(replacement)}</td>
  <td>${escapeHtml(finding.message)}</td>
</tr>`;
    })
    .join("\n");

  const safeRows = rows || '<tr><td colspan="7">No findings. All resources are compatible.</td></tr>';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>K8s Upgrade Validation Report</title>
  <style>
    :root { color-scheme: light; }
    body { font-family: "Segoe UI", Arial, sans-serif; margin: 24px; color: #111; }
    h1 { margin-bottom: 8px; }
    .meta { margin: 0 0 16px; color: #444; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border: 1px solid #d9d9d9; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f5f5f5; }
    .steps li { margin-bottom: 4px; }
  </style>
</head>
<body>
  <h1>K8s Upgrade Validation Report</h1>
  <p class="meta">From v${escapeHtml(report.currentVersion)} to v${escapeHtml(report.targetVersion)} | Generated at ${escapeHtml(report.generatedAt)}</p>
  <p class="meta">Total: ${report.summary.totalResources}, Compatible: ${report.summary.compatible}, Breaking: ${report.summary.breaking}, Warning: ${report.summary.warning}</p>

  <table>
    <thead>
      <tr>
        <th>Severity</th>
        <th>Kind</th>
        <th>Name</th>
        <th>Namespace</th>
        <th>Current API</th>
        <th>Suggested API</th>
        <th>Message</th>
      </tr>
    </thead>
    <tbody>
${safeRows}
    </tbody>
  </table>

  <h2>Upgrade Steps</h2>
  <ol class="steps">
    ${report.upgradeSteps.map((step) => `<li>${escapeHtml(step)}</li>`).join("\n    ")}
  </ol>
</body>
</html>`;
}
