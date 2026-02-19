import { promises as fs } from "node:fs";
import path from "node:path";
import YAML from "yaml";
import { ScanResource } from "./types";

const MANIFEST_EXTENSIONS = new Set([".yaml", ".yml", ".json"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isManifestFile(filePath: string): boolean {
  return MANIFEST_EXTENSIONS.has(path.extname(filePath).toLowerCase());
}

async function collectManifestFiles(entryPath: string): Promise<string[]> {
  const fullPath = path.resolve(entryPath);
  let stat;

  try {
    stat = await fs.stat(fullPath);
  } catch {
    throw new Error(`Manifest path not found: ${entryPath}`);
  }

  if (stat.isFile()) {
    return isManifestFile(fullPath) ? [fullPath] : [];
  }

  if (!stat.isDirectory()) {
    return [];
  }

  const entries = await fs.readdir(fullPath, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map((entry) => collectManifestFiles(path.join(fullPath, entry.name)))
  );

  return nested.flat();
}

function toResource(candidate: unknown, source: string): ScanResource | null {
  if (!isRecord(candidate)) {
    return null;
  }

  const kind = typeof candidate.kind === "string" ? candidate.kind : undefined;
  const apiVersion =
    typeof candidate.apiVersion === "string" ? candidate.apiVersion : undefined;
  const metadata = isRecord(candidate.metadata) ? candidate.metadata : undefined;
  const name = metadata && typeof metadata.name === "string" ? metadata.name : undefined;
  const namespace =
    metadata && typeof metadata.namespace === "string" ? metadata.namespace : undefined;

  if (!kind || !apiVersion || !name) {
    return null;
  }

  if (kind === "List" && Array.isArray(candidate.items)) {
    return null;
  }

  return {
    kind,
    apiVersion,
    name,
    namespace,
    source
  };
}

function extractResources(candidate: unknown, source: string): ScanResource[] {
  if (!isRecord(candidate)) {
    return [];
  }

  const resources: ScanResource[] = [];
  const resource = toResource(candidate, source);

  if (resource) {
    resources.push(resource);
  }

  if (Array.isArray(candidate.items)) {
    for (const item of candidate.items) {
      resources.push(...extractResources(item, source));
    }
  }

  return resources;
}

function filterByNamespaces(
  resources: ScanResource[],
  namespaces: string[]
): ScanResource[] {
  if (namespaces.length === 0) {
    return resources;
  }

  const namespaceSet = new Set(namespaces);

  return resources.filter((resource) => {
    if (!resource.namespace) {
      return true;
    }

    return namespaceSet.has(resource.namespace);
  });
}

export async function scanFromManifestPaths(
  entryPaths: string[],
  namespaces: string[]
): Promise<ScanResource[]> {
  if (entryPaths.length === 0) {
    throw new Error("At least one manifest path must be provided.");
  }

  const collected = await Promise.all(entryPaths.map((entry) => collectManifestFiles(entry)));
  const manifestFiles = Array.from(new Set(collected.flat())).sort();

  if (manifestFiles.length === 0) {
    throw new Error("No manifest files were found. Use .yaml, .yml, or .json files.");
  }

  const resources: ScanResource[] = [];

  for (const filePath of manifestFiles) {
    const raw = await fs.readFile(filePath, "utf8");
    const docs = YAML.parseAllDocuments(raw);

    for (const document of docs) {
      if (document.errors.length > 0) {
        const firstError = document.errors[0];
        throw new Error(`Failed to parse manifest ${filePath}: ${firstError.message}`);
      }

      const parsed = document.toJSON();
      resources.push(
        ...extractResources(parsed, path.relative(process.cwd(), filePath) || filePath)
      );
    }
  }

  const filtered = filterByNamespaces(resources, namespaces);

  return filtered.sort((a, b) => {
    return (
      a.source.localeCompare(b.source) ||
      a.kind.localeCompare(b.kind) ||
      (a.namespace ?? "").localeCompare(b.namespace ?? "") ||
      a.name.localeCompare(b.name)
    );
  });
}
