import fs from "fs";
import path from "path";
import YAML from "yaml";

const ALLOWED_EXTENSIONS = new Set([".md", ".txt", ".json", ".yaml", ".yml"]);

export function ensureFileExists(filePath: string): void {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Error: file not found: ${filePath}. Provide a valid path.`);
  }
}

export function ensureSupportedExtension(filePath: string): void {
  const ext = path.extname(filePath).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    throw new Error(
      `Error: unsupported file type for ${filePath}. Allowed: .md, .txt, .json, .yaml, .yml.`
    );
  }
}

export function readDocumentFile(filePath: string): string {
  ensureFileExists(filePath);
  ensureSupportedExtension(filePath);

  const raw = fs.readFileSync(filePath, "utf8");
  if (!raw.trim()) {
    throw new Error(`Error: input content is empty for ${filePath}. Provide valid content.`);
  }

  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".json") {
    const parsed = JSON.parse(raw);
    return JSON.stringify(parsed, null, 2);
  }
  if (ext === ".yaml" || ext === ".yml") {
    const parsed = YAML.parse(raw);
    return YAML.stringify(parsed).trim();
  }
  return raw;
}

export function readDocuments(files: string[]): { text: string; sources: string[] } {
  if (!files.length) {
    throw new Error("Error: no valid input documents provided. Add at least one document path.");
  }

  const pieces: string[] = [];
  const sources: string[] = [];

  for (const file of files) {
    const content = readDocumentFile(file);
    pieces.push(`\n--- file: ${file} ---\n${content}`);
    sources.push(file);
  }

  return { text: pieces.join("\n"), sources };
}

export function readJsonOrYaml(filePath: string): unknown {
  ensureFileExists(filePath);
  ensureSupportedExtension(filePath);

  const raw = fs.readFileSync(filePath, "utf8");
  if (!raw.trim()) {
    throw new Error(`Error: input content is empty for ${filePath}. Provide valid content.`);
  }

  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".json") {
    return JSON.parse(raw);
  }
  if (ext === ".yaml" || ext === ".yml") {
    return YAML.parse(raw);
  }
  throw new Error(`Error: unsupported registry file type for ${filePath}. Provide JSON or YAML.`);
}

export function writeOutputFile(filePath: string, content: string): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}
