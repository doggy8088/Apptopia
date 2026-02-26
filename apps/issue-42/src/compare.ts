import { Capability, CoverageReport, RegistryData } from "./types";
import { normalizeName } from "./utils";
import { validateRegistry } from "./registry";

function matchByName(target: string, candidate: string): boolean {
  const normalizedTarget = normalizeName(target);
  const normalizedCandidate = normalizeName(candidate);
  return (
    normalizedTarget === normalizedCandidate ||
    normalizedTarget.includes(normalizedCandidate) ||
    normalizedCandidate.includes(normalizedTarget)
  );
}

export function compareCapabilities(
  capabilities: Capability[],
  registry: RegistryData | null
): CoverageReport {
  if (!registry) {
    return {
      registryLoaded: false,
      coverage: capabilities.map((capability) => ({
        capability: capability.name,
        category: capability.category,
        coverage: "unknown",
        matchedSkills: [],
        matchedAgents: [],
        rationale: "Registry not loaded."
      })),
      warnings: ["Registry not loaded; coverage marked as unknown."],
      duplicates: { skills: [], agents: [], cross: [] },
      overlaps: []
    };
  }

  const validation = validateRegistry(registry);
  if (validation.errors.length > 0) {
    return {
      registryLoaded: true,
      coverage: [],
      warnings: validation.errors.map((error) => `Registry error: ${error}`),
      duplicates: validation.duplicates,
      overlaps: validation.overlaps
    };
  }

  const coverage = capabilities.map((capability) => {
    const matchedSkills: string[] = [];
    const matchedAgents: string[] = [];
    const partialMatches: string[] = [];

    for (const skill of registry.skills) {
      if (matchByName(capability.name, skill.name)) {
        matchedSkills.push(skill.name);
      } else if (skill.category && skill.category === capability.category) {
        partialMatches.push(skill.name);
      }
    }

    for (const agent of registry.agents) {
      if (matchByName(capability.name, agent.name)) {
        matchedAgents.push(agent.name);
      } else if (agent.role && normalizeName(agent.role).includes(capability.name)) {
        partialMatches.push(agent.name);
      }
    }

    if (matchedSkills.length > 0 || matchedAgents.length > 0) {
      return {
        capability: capability.name,
        category: capability.category,
        coverage: "covered" as const,
        matchedSkills,
        matchedAgents,
        rationale: "Exact or near-exact name match in registry."
      };
    }

    if (partialMatches.length > 0) {
      return {
        capability: capability.name,
        category: capability.category,
        coverage: "partial" as const,
        matchedSkills: partialMatches,
        matchedAgents: [],
        rationale: "Category or role overlap suggests partial coverage."
      };
    }

    return {
      capability: capability.name,
      category: capability.category,
      coverage: "missing" as const,
      matchedSkills: [],
      matchedAgents: [],
      rationale: "No matching skills or agents found."
    };
  });

  return {
    registryLoaded: true,
    coverage,
    warnings: validation.warnings,
    duplicates: validation.duplicates,
    overlaps: validation.overlaps
  };
}
