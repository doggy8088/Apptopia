import fs from "fs";
import path from "path";
import { analyzeText } from "./analysis";
import { compareCapabilities } from "./compare";
import { generateDefinitions } from "./generate";
import { buildExecutionPlan } from "./plan";
import { loadRegistry, validateRegistry } from "./registry";
import { readDocuments, readJsonOrYaml, writeOutputFile } from "./io";
import {
  formatAnalysisMarkdown,
  formatCoverageMarkdown,
  formatGenerationMarkdown,
  formatPlanMarkdown,
  formatJson,
  formatYaml
} from "./output";
import { ensureArray } from "./utils";
import { AnalysisResult, OutputFormat } from "./types";

interface ParsedArgs {
  command: string | null;
  flags: Record<string, string[]>;
  booleans: Set<string>;
  positionals: string[];
}

function parseArgs(argv: string[]): ParsedArgs {
  const flags: Record<string, string[]> = {};
  const booleans = new Set<string>();
  const positionals: string[] = [];
  let command: string | null = null;

  let i = 0;
  if (argv[0] && !argv[0].startsWith("-")) {
    command = argv[0];
    i = 1;
  }

  while (i < argv.length) {
    const token = argv[i];
    if (token === "-h" || token === "--help") {
      booleans.add("help");
      i += 1;
      continue;
    }

    if (token.startsWith("--")) {
      const withoutPrefix = token.slice(2);
      if (withoutPrefix.includes("=")) {
        const [key, value] = withoutPrefix.split("=");
        flags[key] = flags[key] ?? [];
        flags[key].push(value);
        i += 1;
        continue;
      }

      const next = argv[i + 1];
      if (!next || next.startsWith("--")) {
        booleans.add(withoutPrefix);
        i += 1;
        continue;
      }

      flags[withoutPrefix] = flags[withoutPrefix] ?? [];
      flags[withoutPrefix].push(next);
      i += 2;
      continue;
    }

    positionals.push(token);
    i += 1;
  }

  return { command, flags, booleans, positionals };
}

function showHelp(): void {
  const text = [
    "project-orchestrator <command> [options]",
    "",
    "Commands:",
    "  analyze            Analyze project documents",
    "  compare            Compare capabilities against registry",
    "  generate           Generate skill/agent definitions for missing capabilities",
    "  init-registry      Initialize a registry template",
    "  validate-registry  Validate a registry schema",
    "  plan               Generate an execution plan",
    "  export             Convert analysis output to another format",
    "",
    "Common options:",
    "  --prd <file>        PRD document path",
    "  --spec <file>       Spec document path",
    "  --plan <file>       Plan document path",
    "  --doc <file>        Additional document path (repeatable)",
    "  --registry <file>   Registry file path",
    "  --analysis <file>   Analysis file path",
    "  --format <fmt>      json | yaml | md (default: json)",
    "  --output <file>     Output file path",
    "  --output-dir <dir>  Output directory for generated definitions",
    "  --dry-run           Preview without writing files"
  ].join("\n");
  console.log(text);
}

function getFlag(flags: Record<string, string[]>, key: string): string | undefined {
  const value = flags[key];
  if (!value || value.length === 0) {
    return undefined;
  }
  return value[value.length - 1];
}

function getFlagList(flags: Record<string, string[]>, key: string): string[] {
  return flags[key] ?? [];
}

function parseFormat(value?: string): OutputFormat {
  if (!value) {
    return "json";
  }
  if (value === "json" || value === "yaml" || value === "md") {
    return value;
  }
  throw new Error(`Error: unsupported format '${value}'. Allowed: json, yaml, md.`);
}

function gatherDocuments(flags: Record<string, string[]>): string[] {
  const docs = [
    ...getFlagList(flags, "prd"),
    ...getFlagList(flags, "spec"),
    ...getFlagList(flags, "plan"),
    ...getFlagList(flags, "doc")
  ];
  return docs;
}

function writeOutput(
  content: string,
  outputPath: string | undefined,
  dryRun: boolean
): void {
  if (outputPath) {
    if (dryRun) {
      console.log(`Dry run: would write output to ${outputPath}`);
      return;
    }
    writeOutputFile(outputPath, content);
    return;
  }
  console.log(content);
}

function writeGeneratedOutputs(
  outputDir: string,
  format: OutputFormat,
  generation: ReturnType<typeof generateDefinitions>,
  dryRun: boolean
): void {
  if (dryRun) {
    console.log(`Dry run: would write generated definitions to ${outputDir}`);
    return;
  }

  fs.mkdirSync(outputDir, { recursive: true });
  const skillPath = path.join(outputDir, `skills.${format}`);
  const agentPath = path.join(outputDir, `agents.${format}`);
  const metaPath = path.join(outputDir, `classification.${format}`);

  if (format === "md") {
    writeOutputFile(skillPath, formatGenerationMarkdown({
      classifications: [],
      skillDefinitions: generation.skillDefinitions,
      agentDefinitions: []
    }));
    writeOutputFile(agentPath, formatGenerationMarkdown({
      classifications: [],
      skillDefinitions: [],
      agentDefinitions: generation.agentDefinitions
    }));
    writeOutputFile(metaPath, formatGenerationMarkdown(generation));
  } else if (format === "yaml") {
    writeOutputFile(skillPath, formatYaml(generation.skillDefinitions));
    writeOutputFile(agentPath, formatYaml(generation.agentDefinitions));
    writeOutputFile(metaPath, formatYaml(generation.classifications));
  } else {
    writeOutputFile(skillPath, formatJson(generation.skillDefinitions));
    writeOutputFile(agentPath, formatJson(generation.agentDefinitions));
    writeOutputFile(metaPath, formatJson(generation.classifications));
  }
}

function loadAnalysisFromFile(filePath: string): AnalysisResult {
  const data = readJsonOrYaml(filePath);
  return data as AnalysisResult;
}

async function run(): Promise<void> {
  const parsed = parseArgs(process.argv.slice(2));
  if (parsed.booleans.has("help") || !parsed.command) {
    showHelp();
    return;
  }

  const format = parseFormat(getFlag(parsed.flags, "format"));
  const outputPath = getFlag(parsed.flags, "output");
  const outputDir = getFlag(parsed.flags, "output-dir");
  const dryRun = parsed.booleans.has("dry-run");

  if (parsed.command === "init-registry") {
    const template = {
      version: "1.0.0",
      metadata: {
        createdAt: new Date().toISOString(),
        description: "Skill/Agent registry"
      },
      skills: [],
      agents: []
    };

    const content = format === "md" ? formatJson(template) : format === "yaml" ? formatYaml(template) : formatJson(template);
    writeOutput(content, outputPath, dryRun);
    return;
  }

  if (parsed.command === "validate-registry") {
    const registryPath = getFlag(parsed.flags, "registry");
    if (!registryPath) {
      throw new Error("Error: registry path is required for validate-registry.");
    }
    const registry = loadRegistry(registryPath);
    if (!registry) {
      throw new Error("Error: registry could not be loaded.");
    }

    const validation = validateRegistry(registry);
    if (validation.errors.length > 0) {
      console.error(`Error: invalid registry schema. ${validation.errors.join(" ")}`);
      process.exitCode = 1;
      return;
    }
    const report = {
      status: "ok",
      warnings: validation.warnings,
      duplicates: validation.duplicates,
      overlaps: validation.overlaps
    };
    writeOutput(format === "yaml" ? formatYaml(report) : formatJson(report), outputPath, dryRun);
    return;
  }

  if (parsed.command === "export") {
    const inputPath = getFlag(parsed.flags, "input") ?? getFlag(parsed.flags, "analysis");
    if (!inputPath) {
      throw new Error("Error: export requires --input or --analysis file path.");
    }
    const data = readJsonOrYaml(inputPath);
    let content: string;
    if (format === "yaml") {
      content = formatYaml(data);
    } else if (format === "json") {
      content = formatJson(data);
    } else {
      throw new Error("Error: Markdown format is not supported for the 'export' command.");
    }
    writeOutput(content, outputPath, dryRun);
    return;
  }

  if (parsed.command === "analyze") {
    const docFiles = gatherDocuments(parsed.flags);
    const { text, sources } = readDocuments(docFiles);
    const analysis = analyzeText(text, sources);
    const content =
      format === "md" ? formatAnalysisMarkdown(analysis) : format === "yaml" ? formatYaml(analysis) : formatJson(analysis);
    writeOutput(content, outputPath, dryRun);
    return;
  }

  if (parsed.command === "compare") {
    const docFiles = gatherDocuments(parsed.flags);
    const analysisPath = getFlag(parsed.flags, "analysis");
    const registryPath = getFlag(parsed.flags, "registry");

    const analysis = analysisPath
      ? loadAnalysisFromFile(analysisPath)
      : (() => {
          const { text, sources } = readDocuments(docFiles);
          return analyzeText(text, sources);
        })();

    const registry = registryPath ? loadRegistry(registryPath) : null;
    const report = compareCapabilities(analysis.requiredCapabilities, registry);
    const content =
      format === "md" ? formatCoverageMarkdown(report) : format === "yaml" ? formatYaml(report) : formatJson(report);
    writeOutput(content, outputPath, dryRun);
    return;
  }

  if (parsed.command === "generate") {
    const docFiles = gatherDocuments(parsed.flags);
    const analysisPath = getFlag(parsed.flags, "analysis");
    const registryPath = getFlag(parsed.flags, "registry");

    const analysis = analysisPath
      ? loadAnalysisFromFile(analysisPath)
      : (() => {
          const { text, sources } = readDocuments(docFiles);
          return analyzeText(text, sources);
        })();

    const registry = registryPath ? loadRegistry(registryPath) : null;
    const report = compareCapabilities(analysis.requiredCapabilities, registry);
    const missing = analysis.requiredCapabilities.filter((capability) => {
      const coverage = report.coverage.find((item) => item.capability === capability.name);
      return coverage?.coverage === "missing" || coverage?.coverage === "unknown";
    });

    const generation = generateDefinitions(missing);

    if (outputDir) {
      writeGeneratedOutputs(outputDir, format, generation, dryRun);
      return;
    }

    const content =
      format === "md" ? formatGenerationMarkdown(generation) : format === "yaml" ? formatYaml(generation) : formatJson(generation);
    writeOutput(content, outputPath, dryRun);
    return;
  }

  if (parsed.command === "plan") {
    const docFiles = gatherDocuments(parsed.flags);
    const analysisPath = getFlag(parsed.flags, "analysis");

    const analysis = analysisPath
      ? loadAnalysisFromFile(analysisPath)
      : (() => {
          const { text, sources } = readDocuments(docFiles);
          return analyzeText(text, sources);
        })();

    const plan = buildExecutionPlan(analysis);
    const content =
      format === "md" ? formatPlanMarkdown(plan) : format === "yaml" ? formatYaml(plan) : formatJson(plan);
    writeOutput(content, outputPath, dryRun);
    return;
  }

  throw new Error(`Error: unknown command '${parsed.command}'. Use --help for usage.`);
}

run().catch((error: Error) => {
  console.error(error.message);
  process.exitCode = 1;
});
