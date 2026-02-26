import {
  Capability,
  ClassificationDecision,
  GenerationResult,
  SkillDefinition,
  AgentDefinition
} from "./types";
import { lookupCapability } from "./taxonomy";
import { normalizeName } from "./utils";

function classifyCapability(capability: Capability): ClassificationDecision {
  const known = lookupCapability(capability.name);
  const complexity = known?.complexity ?? capability.complexity;

  if (complexity === "complex" || /plan|orchestr|strategy|execution/i.test(capability.name)) {
    return {
      capability: capability.name,
      category: capability.category,
      recommendedType: "agent",
      rationale:
        "Capability requires multi-step decisions or coordination across skills, so an agent is recommended."
    };
  }

  return {
    capability: capability.name,
    category: capability.category,
    recommendedType: "skill",
    rationale: "Capability is a focused, repeatable task with stable inputs/outputs, so a skill is recommended."
  };
}

function buildSkillDefinition(capability: Capability): SkillDefinition {
  const id = `skill-${normalizeName(capability.name)}`;
  return {
    id,
    name: `${normalizeName(capability.name)}-skill`,
    version: "1.0.0",
    category: capability.category,
    purpose: capability.description,
    trigger_conditions: [
      `When project scope requires ${capability.name.replace(/_/g, " ")}.`,
      "When analysis output is missing structured capability details."
    ],
    input_schema: {
      type: "object",
      required: ["context"],
      properties: {
        context: { type: "string", description: "Relevant project context or requirement snippet." },
        constraints: { type: "array", items: { type: "string" } }
      }
    },
    output_schema: {
      type: "object",
      required: ["result"],
      properties: {
        result: { type: "string", description: "Structured output for the capability." },
        evidence: { type: "array", items: { type: "string" } }
      }
    },
    constraints: [
      "Do not invent requirements not present in the input.",
      "Return explicit unknowns when information is missing."
    ],
    examples: [
      {
        input: { context: "PRD excerpt about registry validation" },
        output: { result: "Validation checklist for registry schema" }
      }
    ],
    failure_modes: [
      "Input context is insufficient to derive a reliable output.",
      "Conflicting requirements detected in source documents."
    ]
  };
}

function buildAgentDefinition(capability: Capability): AgentDefinition {
  const id = `agent-${normalizeName(capability.name)}`;
  return {
    id,
    name: `${normalizeName(capability.name)}-agent`,
    version: "1.0.0",
    role: `Coordinate ${capability.description.toLowerCase()}.`,
    responsibilities: [
      `Decompose ${capability.name.replace(/_/g, " ")} into ordered tasks.`,
      "Select and invoke appropriate skills.",
      "Summarize outputs and escalate uncertainties."
    ],
    decision_scope: [
      "Sequence tasks and resolve dependencies.",
      "Determine when to stop or request clarification."
    ],
    allowed_skills: ["requirement-analysis-skill", "capability-mapping-skill"],
    disallowed_actions: ["Execute changes without explicit approval.", "Assume missing requirements."],
    escalation_rules: ["Escalate when critical inputs are missing or conflicts remain unresolved."],
    output_contract: "Provide a structured plan and decision log for downstream orchestration.",
    collaboration_rules: ["Coordinate with governance agents for registry updates."]
  };
}

export function generateDefinitions(missingCapabilities: Capability[]): GenerationResult {
  const classifications: ClassificationDecision[] = [];
  const skillDefinitions: SkillDefinition[] = [];
  const agentDefinitions: AgentDefinition[] = [];

  for (const capability of missingCapabilities) {
    const decision = classifyCapability(capability);
    classifications.push(decision);

    if (decision.recommendedType === "skill") {
      skillDefinitions.push(buildSkillDefinition(capability));
    } else {
      agentDefinitions.push(buildAgentDefinition(capability));
    }
  }

  return { classifications, skillDefinitions, agentDefinitions };
}
