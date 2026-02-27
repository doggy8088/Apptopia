export type OutputFormat = "json" | "yaml" | "md";

export interface Capability {
  name: string;
  category: string;
  description: string;
  complexity: "simple" | "complex";
  evidence: string[];
}

export interface AnalysisResult {
  projectType: string;
  summary: string;
  modules: string[];
  technicalDomains: string[];
  requiredCapabilities: Capability[];
  dependencies: string[];
  risks: string[];
  sourceFiles: string[];
  createdAt: string;
}

export interface RegistrySkill {
  name: string;
  category?: string;
  version?: string;
  purpose?: string;
}

export interface RegistryAgent {
  name: string;
  role?: string;
  version?: string;
}

export interface RegistryData {
  version?: string;
  metadata?: Record<string, unknown>;
  taxonomy?: Record<string, unknown>;
  skills: RegistrySkill[];
  agents: RegistryAgent[];
}

export type CoverageStatus = "covered" | "partial" | "missing" | "unknown";

export interface CapabilityCoverage {
  capability: string;
  category: string;
  coverage: CoverageStatus;
  matchedSkills: string[];
  matchedAgents: string[];
  rationale: string;
}

export interface CoverageReport {
  registryLoaded: boolean;
  coverage: CapabilityCoverage[];
  warnings: string[];
  duplicates: {
    skills: string[];
    agents: string[];
    cross: string[];
  };
  overlaps: string[];
}

export interface ClassificationDecision {
  capability: string;
  category: string;
  recommendedType: "skill" | "agent";
  rationale: string;
}

export interface SkillDefinition {
  id: string;
  name: string;
  version: string;
  category: string;
  purpose: string;
  trigger_conditions: string[];
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  constraints: string[];
  examples: Array<Record<string, unknown>>;
  failure_modes: string[];
}

export interface AgentDefinition {
  id: string;
  name: string;
  version: string;
  role: string;
  responsibilities: string[];
  decision_scope: string[];
  allowed_skills: string[];
  disallowed_actions: string[];
  escalation_rules: string[];
  output_contract: string;
  collaboration_rules: string[];
}

export interface GenerationResult {
  classifications: ClassificationDecision[];
  skillDefinitions: SkillDefinition[];
  agentDefinitions: AgentDefinition[];
}

export interface ExecutionStep {
  id: string;
  name: string;
  owner: string;
  required_skills: string[];
  input_dependencies: string[];
  expected_output: string;
  retry_behavior: string;
  review_points: string[];
}

export interface ExecutionPlan {
  steps: ExecutionStep[];
  dependencies: Array<{ from: string; to: string }>;
  owners: string[];
}
