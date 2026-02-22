import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { Note } from "./types";
import { normalizeKey, stripExtension, toPosixPath, uniqueStrings } from "./utils";

interface FrontmatterResult {
  frontmatter: Record<string, unknown>;
  body: string;
  warnings: string[];
}

export async function scanVault(vaultPath: string): Promise<{ notes: Note[]; warnings: string[] }> {
  const markdownFiles = await listMarkdownFiles(vaultPath);
  const warnings: string[] = [];
  const notes: Note[] = [];

  for (const filePath of markdownFiles) {
    const raw = await fs.readFile(filePath, "utf8");
    const relativePath = toPosixPath(path.relative(vaultPath, filePath));
    const parsed = parseFrontmatter(raw, relativePath);

    warnings.push(...parsed.warnings);

    const filename = path.basename(filePath);
    const title = stripExtension(filename);
    const id = stripExtension(relativePath);

    const tags = extractTags(parsed.frontmatter, parsed.body);
    const aliases = extractAliases(parsed.frontmatter);
    const links = extractWikilinks(parsed.body);
    const embeds = extractEmbeds(parsed.body);

    notes.push({
      id,
      title,
      path: filePath,
      relativePath,
      body: parsed.body,
      frontmatter: parsed.frontmatter,
      tags,
      links,
      embeds,
      aliases
    });
  }

  return { notes, warnings };
}

async function listMarkdownFiles(root: string): Promise<string[]> {
  const entries = await fs.readdir(root, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }

    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await listMarkdownFiles(fullPath)));
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".md")) {
      files.push(fullPath);
    }
  }

  return files;
}

function parseFrontmatter(raw: string, relativePath: string): FrontmatterResult {
  const warnings: string[] = [];
  const lines = raw.split(/\r?\n/);

  if (lines.length > 0 && lines[0].trim() === "---") {
    const endIndex = lines.slice(1).findIndex((line) => line.trim() === "---");
    if (endIndex !== -1) {
      const frontmatterRaw = lines.slice(1, endIndex + 1).join("\n");
      const body = lines.slice(endIndex + 2).join("\n");
      try {
        const parsed = yaml.parse(frontmatterRaw) ?? {};
        if (typeof parsed === "object" && parsed !== null) {
          return { frontmatter: parsed as Record<string, unknown>, body, warnings };
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        warnings.push(`Frontmatter parse failed for ${relativePath}: ${message}`);
      }
    }
  }

  return { frontmatter: {}, body: raw, warnings };
}

function extractTags(frontmatter: Record<string, unknown>, body: string): string[] {
  const tags: string[] = [];
  const rawTags = frontmatter.tags ?? frontmatter.tag;

  if (Array.isArray(rawTags)) {
    for (const tag of rawTags) {
      if (typeof tag === "string") {
        tags.push(normalizeKey(tag.replace(/^#/, "")));
      }
    }
  } else if (typeof rawTags === "string") {
    const split = rawTags.split(/[,\s]+/).filter(Boolean);
    for (const tag of split) {
      tags.push(normalizeKey(tag.replace(/^#/, "")));
    }
  }

  const tagRegex = /(^|\s)#([A-Za-z0-9_-]+)/g;
  let match: RegExpExecArray | null;
  while ((match = tagRegex.exec(body)) !== null) {
    tags.push(normalizeKey(match[2]));
  }

  return uniqueStrings(tags);
}

function extractAliases(frontmatter: Record<string, unknown>): string[] {
  const aliases: string[] = [];
  const rawAliases = frontmatter.aliases ?? frontmatter.alias;

  if (Array.isArray(rawAliases)) {
    for (const alias of rawAliases) {
      if (typeof alias === "string") {
        aliases.push(alias);
      }
    }
  } else if (typeof rawAliases === "string") {
    const split = rawAliases.split(/[,\n]+/).map((entry) => entry.trim());
    for (const alias of split) {
      if (alias) {
        aliases.push(alias);
      }
    }
  }

  return uniqueStrings(aliases);
}

function extractWikilinks(body: string): string[] {
  const regex = /\[\[([^\]]+)\]\]/g;
  const links: string[] = [];
  let match: RegExpExecArray | null;

  while ((match = regex.exec(body)) !== null) {
    const startIndex = match.index ?? 0;
    if (startIndex > 0 && body[startIndex - 1] === "!") {
      continue;
    }
    links.push(match[1]);
  }

  return uniqueStrings(links);
}

function extractEmbeds(body: string): string[] {
  const regex = /!\[\[([^\]]+)\]\]/g;
  const embeds: string[] = [];
  let match: RegExpExecArray | null;

  while ((match = regex.exec(body)) !== null) {
    embeds.push(match[1]);
  }

  return uniqueStrings(embeds);
}
