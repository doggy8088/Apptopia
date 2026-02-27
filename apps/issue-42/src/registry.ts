import { RegistryData } from "./types";
import { readJsonOrYaml } from "./io";
import { normalizeName, uniqueStrings } from "./utils";

export function loadRegistry(filePath?: string): RegistryData | null {
  if (!filePath) {
    return null;
  }
  const data = readJsonOrYaml(filePath);
  return data as RegistryData;
}

export interface RegistryValidationResult {
  errors: string[];
  warnings: string[];
  duplicates: {
    skills: string[];
    agents: string[];
    cross: string[];
  };
  overlaps: string[];
}

function collectDuplicates(items: Array<{ name: string }>): string[] {
  const counts = new Map<string, number>();
  for (const item of items) {
    const normalized = normalizeName(item.name);
    counts.set(normalized, (counts.get(normalized) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .filter(([, count]) => count > 1)
    .map(([name]) => name);
}

export function validateRegistry(data: RegistryData): RegistryValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== "object") {
    errors.push("Registry must be an object.");
  }

  if (!Array.isArray(data.skills)) {
    errors.push("Registry schema invalid: expected 'skills' array.");
  }

  if (!Array.isArray(data.agents)) {
    errors.push("Registry schema invalid: expected 'agents' array.");
  }

  if (errors.length > 0) {
    return {
      errors,
      warnings,
      duplicates: { skills: [], agents: [], cross: [] },
      overlaps: []
    };
  }

  const skillNames = data.skills.map((skill) => skill.name).filter(Boolean);
  const agentNames = data.agents.map((agent) => agent.name).filter(Boolean);

  if (skillNames.length !== data.skills.length) {
    errors.push("Registry schema invalid: all skills must include a 'name'.");
  }

  if (agentNames.length !== data.agents.length) {
    errors.push("Registry schema invalid: all agents must include a 'name'.");
  }

  if (errors.length > 0) {
    return {
      errors,
      warnings,
      duplicates: { skills: [], agents: [], cross: [] },
      overlaps: []
    };
  }

  const duplicates = {
    skills: collectDuplicates(data.skills),
    agents: collectDuplicates(data.agents),
    cross: [] as string[]
  };

  const skillSet = new Set(skillNames.map(normalizeName));
  const agentSet = new Set(agentNames.map(normalizeName));
  const cross: string[] = [];
  for (const name of skillSet) {
    if (agentSet.has(name)) {
      cross.push(name);
    }
  }
  duplicates.cross = cross;

  if (duplicates.skills.length > 0) {
    warnings.push(`Duplicate skill names detected: ${duplicates.skills.join(", ")}.`);
  }
  if (duplicates.agents.length > 0) {
    warnings.push(`Duplicate agent names detected: ${duplicates.agents.join(", ")}.`);
  }
  if (duplicates.cross.length > 0) {
    warnings.push(`Skill/agent name overlap detected: ${duplicates.cross.join(", ")}.`);
  }

  const overlaps: string[] = [];
  const categoryMap = new Map<string, string[]>();
  for (const skill of data.skills) {
    if (skill.category) {
      const existing = categoryMap.get(skill.category) ?? [];
      existing.push(skill.name);
      categoryMap.set(skill.category, existing);
    }
  }
  for (const [category, names] of categoryMap.entries()) {
    if (names.length > 3) {
      overlaps.push(`High overlap in category '${category}': ${uniqueStrings(names).join(", ")}.`);
    }
  }

  return { errors, warnings, duplicates, overlaps };
}
