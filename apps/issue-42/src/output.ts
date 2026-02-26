import YAML from "yaml";
import {
  AnalysisResult,
  CoverageReport,
  GenerationResult,
  ExecutionPlan,
  OutputFormat
} from "./types";

export function formatJson(data: unknown): string {
  return JSON.stringify(data, null, 2);
}

export function formatYaml(data: unknown): string {
  return YAML.stringify(data).trim();
}

export function formatAnalysisMarkdown(analysis: AnalysisResult): string {
  return [
    `# Capability Analysis`,
    ``,
    `- Project Type: ${analysis.projectType}`,
    `- Summary: ${analysis.summary}`,
    `- Sources: ${analysis.sourceFiles.join(", ")}`,
    ``,
    `## Modules`,
    analysis.modules.length ? analysis.modules.map((mod) => `- ${mod}`).join("\n") : "- (none)",
    ``,
    `## Technical Domains`,
    analysis.technicalDomains.length
      ? analysis.technicalDomains.map((domain) => `- ${domain}`).join("\n")
      : "- (none)",
    ``,
    `## Required Capabilities`,
    analysis.requiredCapabilities
      .map((capability) => `- ${capability.name} (${capability.category})`)
      .join("\n"),
    ``,
    `## Dependencies`,
    analysis.dependencies.length ? analysis.dependencies.map((dep) => `- ${dep}`).join("\n") : "- (none)",
    ``,
    `## Risks`,
    analysis.risks.length ? analysis.risks.map((risk) => `- ${risk}`).join("\n") : "- (none)"
  ].join("\n");
}

export function formatCoverageMarkdown(report: CoverageReport): string {
  const coverageLines = report.coverage.length
    ? report.coverage.map((item) => {
        const matches = [...item.matchedSkills, ...item.matchedAgents];
        const matchInfo = matches.length ? ` (matches: ${matches.join(", ")})` : "";
        return `- ${item.capability}: ${item.coverage}${matchInfo}`;
      })
    : ["- (no coverage results)"];

  const warningLines = report.warnings.length
    ? report.warnings.map((warning) => `- ${warning}`)
    : ["- (none)"];

  const overlapLines = report.overlaps.length
    ? report.overlaps.map((overlap) => `- ${overlap}`)
    : ["- (none)"];

  return [
    `# Coverage Report`,
    ``,
    `- Registry Loaded: ${report.registryLoaded ? "yes" : "no"}`,
    ``,
    `## Coverage`,
    ...coverageLines,
    ``,
    `## Warnings`,
    ...warningLines,
    ``,
    `## Overlaps`,
    ...overlapLines
  ].join("\n");
}

export function formatGenerationMarkdown(result: GenerationResult): string {
  const classificationLines = result.classifications.length
    ? result.classifications.map(
        (item) => `- ${item.capability}: ${item.recommendedType} (${item.rationale})`
      )
    : ["- (none)"];

  const skillLines = result.skillDefinitions.length
    ? result.skillDefinitions.map((skill) => `- ${skill.name} (${skill.category})`)
    : ["- (none)"];

  const agentLines = result.agentDefinitions.length
    ? result.agentDefinitions.map((agent) => `- ${agent.name}`)
    : ["- (none)"];

  return [
    `# Generated Definitions`,
    ``,
    `## Classification`,
    ...classificationLines,
    ``,
    `## Skills`,
    ...skillLines,
    ``,
    `## Agents`,
    ...agentLines
  ].join("\n");
}

export function formatPlanMarkdown(plan: ExecutionPlan): string {
  const stepLines = plan.steps.map(
    (step) =>
      `- ${step.id}: ${step.name} (owner: ${step.owner})\n  - required_skills: ${
        step.required_skills.length ? step.required_skills.join(", ") : "(none)"
      }\n  - expected_output: ${step.expected_output}`
  );

  const dependencyLines = plan.dependencies.map((dep) => `- ${dep.from} -> ${dep.to}`);

  return [
    `# Execution Plan`,
    ``,
    `## Steps`,
    ...stepLines,
    ``,
    `## Dependencies`,
    ...(dependencyLines.length ? dependencyLines : ["- (none)"])
  ].join("\n");
}

export function formatOutput(format: OutputFormat, data: unknown): string {
  if (format === "yaml") {
    return formatYaml(data);
  }
  if (format === "md") {
    return typeof data === "string" ? data : formatJson(data);
  }
  return formatJson(data);
}
