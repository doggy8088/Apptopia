import { Capability } from "./types";

interface CapabilityDefinition {
  name: string;
  category: string;
  description: string;
  complexity: "simple" | "complex";
  keywords: string[];
}

const DEFAULT_CAPABILITIES: CapabilityDefinition[] = [
  {
    name: "requirement_analysis",
    category: "analysis",
    description: "Extract goals, constraints, and scope from project documents",
    complexity: "simple",
    keywords: ["requirement", "prd", "spec", "需求", "目標", "analysis", "analyze"]
  },
  {
    name: "capability_mapping",
    category: "planning",
    description: "Map requirements to a capability taxonomy",
    complexity: "simple",
    keywords: ["capability", "taxonomy", "mapping", "能力", "分類"]
  },
  {
    name: "registry_comparison",
    category: "analysis",
    description: "Compare required capabilities with existing registries",
    complexity: "simple",
    keywords: ["registry", "compare", "coverage", "比對", "覆蓋"]
  },
  {
    name: "skill_definition_generation",
    category: "factory",
    description: "Generate reusable skill definitions",
    complexity: "simple",
    keywords: ["skill", "definition", "generate skill", "技能"]
  },
  {
    name: "agent_definition_generation",
    category: "factory",
    description: "Generate multi-step agent definitions",
    complexity: "complex",
    keywords: ["agent", "definition", "generate agent", "代理"]
  },
  {
    name: "execution_planning",
    category: "planning",
    description: "Produce execution plans with dependencies and owners",
    complexity: "complex",
    keywords: ["plan", "execution", "orchestr", "流程", "計畫"]
  },
  {
    name: "registry_governance",
    category: "governance",
    description: "Validate, version, and manage skill/agent registries",
    complexity: "simple",
    keywords: ["governance", "validate", "version", "metadata", "治理", "校驗"]
  }
];

export function getDefaultCapabilities(): CapabilityDefinition[] {
  return DEFAULT_CAPABILITIES.map((capability) => ({ ...capability }));
}

function matchesKeyword(text: string, keyword: string): boolean {
  if (!keyword) {
    return false;
  }
  const pattern = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(pattern, "i");
  return regex.test(text);
}

export function extractCapabilities(text: string): Capability[] {
  const definitions = getDefaultCapabilities();
  const matched: Capability[] = [];

  for (const definition of definitions) {
    const evidence = definition.keywords.filter((keyword) => matchesKeyword(text, keyword));
    if (evidence.length > 0) {
      matched.push({
        name: definition.name,
        category: definition.category,
        description: definition.description,
        complexity: definition.complexity,
        evidence
      });
    }
  }

  if (matched.length === 0) {
    const fallback = definitions.filter((capability) =>
      ["requirement_analysis", "capability_mapping"].includes(capability.name)
    );
    for (const definition of fallback) {
      matched.push({
        name: definition.name,
        category: definition.category,
        description: definition.description,
        complexity: definition.complexity,
        evidence: ["default"]
      });
    }
  }

  const unique = new Map<string, Capability>();
  for (const cap of matched) {
    unique.set(cap.name, cap);
  }
  return Array.from(unique.values());
}

export function lookupCapability(name: string): CapabilityDefinition | undefined {
  return DEFAULT_CAPABILITIES.find((capability) => capability.name === name);
}
