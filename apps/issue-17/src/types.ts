export type OutputFormat = "text" | "json" | "html";

export interface ScanResource {
  apiVersion: string;
  kind: string;
  name: string;
  namespace?: string;
  source: string;
}

export interface ApiRule {
  id: string;
  kind: string;
  apiVersion: string;
  replacementApiVersion?: string;
  deprecatedIn?: string;
  removedIn?: string;
  changedIn?: string;
  reason: string;
  migration?: string;
}

export type FindingSeverity = "breaking" | "warning";

export interface Finding {
  severity: FindingSeverity;
  resource: ScanResource;
  rule: ApiRule;
  message: string;
}

export interface ReportSummary {
  totalResources: number;
  breaking: number;
  warning: number;
  compatible: number;
  overall: "compatible" | "action-required";
}

export interface UpgradeReport {
  tool: {
    name: string;
    version: string;
    mode: "manifest" | "cluster";
  };
  currentVersion: string;
  targetVersion: string;
  generatedAt: string;
  summary: ReportSummary;
  findings: Finding[];
  upgradeSteps: string[];
}

export interface CliOptions {
  currentVersion: string;
  targetVersion: string;
  kubeconfig?: string;
  namespaces: string[];
  manifestPaths: string[];
  output: OutputFormat;
  outputFile?: string;
}

export interface ReporterIO {
  stdout: (message: string) => void;
  stderr: (message: string) => void;
}
