import { AnalysisResult } from "./types";
import { chunkText, uniqueStrings } from "./utils";
import { extractCapabilities } from "./taxonomy";

interface ContentSignals {
  hasGoal: boolean;
  hasModules: boolean;
  hasTechScope: boolean;
  hasProcess: boolean;
  hasNonFunctional: boolean;
}

const GOAL_KEYWORDS = ["goal", "objective", "目標", "目的", "summary", "背景", "problem"];
const MODULE_KEYWORDS = ["module", "feature", "功能", "模組", "workflow", "component"];
const TECH_KEYWORDS = ["tech", "stack", "architecture", "技術", "範圍", "domain", "api", "cli"];
const PROCESS_KEYWORDS = ["process", "flow", "流程", "步驟", "pipeline", "orchestr"];
const NONFUNCTIONAL_KEYWORDS = [
  "performance",
  "security",
  "availability",
  "scalability",
  "latency",
  "non-functional",
  "可靠",
  "安全",
  "效能"
];

function includesKeyword(text: string, keyword: string): boolean {
  const pattern = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(pattern, "i").test(text);
}

function detectSignals(text: string): ContentSignals {
  const hasGoal = GOAL_KEYWORDS.some((keyword) => includesKeyword(text, keyword));
  const hasModules = MODULE_KEYWORDS.some((keyword) => includesKeyword(text, keyword));
  const hasTechScope = TECH_KEYWORDS.some((keyword) => includesKeyword(text, keyword));
  const hasProcess = PROCESS_KEYWORDS.some((keyword) => includesKeyword(text, keyword));
  const hasNonFunctional = NONFUNCTIONAL_KEYWORDS.some((keyword) => includesKeyword(text, keyword));

  return { hasGoal, hasModules, hasTechScope, hasProcess, hasNonFunctional };
}

function extractModules(text: string): string[] {
  const lines = text.split(/\r?\n/);
  const modules: string[] = [];
  let capture = false;
  let captureBudget = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (captureBudget > 0) {
        captureBudget -= 1;
      }
      continue;
    }

    if (/^#{1,6}\s*(功能|modules?|features?|模組)/i.test(trimmed)) {
      capture = true;
      captureBudget = 12;
      continue;
    }

    if (/^(\-|\*|\d+\.)\s+/.test(trimmed) && capture && captureBudget > 0) {
      modules.push(trimmed.replace(/^(\-|\*|\d+\.)\s+/, ""));
      continue;
    }

    if (capture && captureBudget > 0 && /功能|feature|module/i.test(trimmed)) {
      modules.push(trimmed);
      continue;
    }

    if (captureBudget > 0) {
      captureBudget -= 1;
    } else {
      capture = false;
    }
  }

  return uniqueStrings(modules).slice(0, 10);
}

function extractTechnicalDomains(text: string): string[] {
  const domains: Array<[string, string[]]> = [
    ["cli", ["cli", "command line"]],
    ["registry", ["registry", "catalog", "capability taxonomy"]],
    ["orchestration", ["orchestr", "workflow", "pipeline"]],
    ["analysis", ["analysis", "requirement", "spec", "prd"]],
    ["generation", ["generate", "definition", "template"]],
    ["governance", ["governance", "version", "metadata", "validate"]]
  ];

  const hits: string[] = [];
  for (const [label, keys] of domains) {
    if (keys.some((keyword) => includesKeyword(text, keyword))) {
      hits.push(label);
    }
  }
  return uniqueStrings(hits);
}

function extractDependencies(text: string): string[] {
  const lines = text.split(/\r?\n/);
  const deps: string[] = [];
  for (const line of lines) {
    if (/依賴|dependency|depends on/i.test(line)) {
      deps.push(line.trim());
    }
  }
  return uniqueStrings(deps).slice(0, 5);
}

function extractRisks(text: string): string[] {
  const lines = text.split(/\r?\n/);
  const risks: string[] = [];
  for (const line of lines) {
    if (/risk|風險|uncertainty|不確定/i.test(line)) {
      risks.push(line.trim());
    }
  }
  return uniqueStrings(risks).slice(0, 5);
}

function extractProjectType(text: string): string {
  if (/cli|command line/i.test(text)) {
    return "cli tool";
  }
  if (/api|server|backend/i.test(text)) {
    return "backend service";
  }
  if (/frontend|web|ui/i.test(text)) {
    return "web application";
  }
  return "software project";
}

function summarizeText(text: string): string {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return "";
  }
  const sentenceMatch = cleaned.match(/[^.!?。！？]+[.!?。！？]/g);
  if (sentenceMatch && sentenceMatch.length > 0) {
    return chunkText(sentenceMatch.slice(0, 2).join(" "), 320);
  }
  return chunkText(cleaned, 320);
}

function validateContent(text: string): void {
  const signals = detectSignals(text);
  const score = [
    signals.hasGoal,
    signals.hasModules,
    signals.hasTechScope,
    signals.hasProcess,
    signals.hasNonFunctional
  ].filter(Boolean).length;

  if (score < 2) {
    throw new Error(
      "Error: input content is insufficient for project analysis. Missing project goal, module details, technical scope, process description, or non-functional requirements."
    );
  }
}

export function analyzeText(text: string, sources: string[], now: Date = new Date()): AnalysisResult {
  validateContent(text);
  const capabilities = extractCapabilities(text);

  return {
    projectType: extractProjectType(text),
    summary: summarizeText(text),
    modules: extractModules(text),
    technicalDomains: extractTechnicalDomains(text),
    requiredCapabilities: capabilities,
    dependencies: extractDependencies(text),
    risks: extractRisks(text),
    sourceFiles: sources,
    createdAt: now.toISOString()
  };
}
