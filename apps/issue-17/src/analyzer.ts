import { API_RULES } from "./rules";
import { ApiRule, Finding, FindingSeverity, ScanResource } from "./types";
import { K8sVersion, compareK8sVersion, parseMilestone } from "./version";

function ruleMatchesResource(rule: ApiRule, resource: ScanResource): boolean {
  return rule.apiVersion === resource.apiVersion && rule.kind === resource.kind;
}

function isMilestoneReached(target: K8sVersion, milestone?: string): boolean {
  if (!milestone) {
    return false;
  }

  return compareK8sVersion(target, parseMilestone(milestone)) >= 0;
}

function severityRank(severity: FindingSeverity): number {
  return severity === "breaking" ? 2 : 1;
}

function buildMessage(resource: ScanResource, rule: ApiRule, severity: FindingSeverity): string {
  if (severity === "breaking") {
    const migration = rule.replacementApiVersion
      ? ` Migrate to \"${rule.replacementApiVersion}\".`
      : "";
    return `API version \"${resource.apiVersion}\" for ${resource.kind} is removed in v${rule.removedIn}.${migration}`;
  }

  if (rule.deprecatedIn) {
    const migration = rule.replacementApiVersion
      ? ` Consider migrating to \"${rule.replacementApiVersion}\".`
      : "";
    return `API version \"${resource.apiVersion}\" for ${resource.kind} is deprecated since v${rule.deprecatedIn}.${migration}`;
  }

  return `API version \"${resource.apiVersion}\" for ${resource.kind} has compatibility changes.`;
}

function evaluateRule(target: K8sVersion, rule: ApiRule): FindingSeverity | null {
  if (isMilestoneReached(target, rule.removedIn)) {
    return "breaking";
  }

  if (isMilestoneReached(target, rule.deprecatedIn) || isMilestoneReached(target, rule.changedIn)) {
    return "warning";
  }

  return null;
}

export function analyzeResources(
  resources: ScanResource[],
  targetVersion: K8sVersion,
  rules: ApiRule[] = API_RULES
): Finding[] {
  const findings: Finding[] = [];

  for (const resource of resources) {
    const matchedRules = rules.filter((rule) => ruleMatchesResource(rule, resource));

    let selected: { rule: ApiRule; severity: FindingSeverity } | null = null;

    for (const rule of matchedRules) {
      const severity = evaluateRule(targetVersion, rule);
      if (!severity) {
        continue;
      }

      if (!selected || severityRank(severity) > severityRank(selected.severity)) {
        selected = { rule, severity };
      }
    }

    if (!selected) {
      continue;
    }

    findings.push({
      severity: selected.severity,
      resource,
      rule: selected.rule,
      message: buildMessage(resource, selected.rule, selected.severity)
    });
  }

  return findings.sort((a, b) => {
    const severityDelta = severityRank(b.severity) - severityRank(a.severity);
    if (severityDelta !== 0) {
      return severityDelta;
    }

    return (
      a.resource.kind.localeCompare(b.resource.kind) ||
      (a.resource.namespace ?? "").localeCompare(b.resource.namespace ?? "") ||
      a.resource.name.localeCompare(b.resource.name)
    );
  });
}
