import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { buildBookPlan, renderBookMarkdown } from "./book";
import { renderNote } from "./converter";
import { filterNotes } from "./filter";
import { buildGraph, createNoteIndex, orderNotes } from "./graph";
import { writeOutput } from "./output";
import { AssetRef, BookConfig, Note, OutputFormat, ReporterIO } from "./types";
import { scanVault } from "./vault";

export interface RunOptions {
  vault: string;
  topic: string;
  configPath?: string;
  outputDir: string;
  outputFormat: OutputFormat;
  language?: string;
  dryRun: boolean;
}

const defaultIO: ReporterIO = {
  stdout: (message: string) => {
    process.stdout.write(message);
  },
  stderr: (message: string) => {
    process.stderr.write(message);
  }
};

export async function runWithOptions(options: RunOptions, io: ReporterIO = defaultIO): Promise<number> {
  const vaultPath = path.resolve(options.vault);
  const outputDir = path.resolve(options.outputDir);

  await assertDirectory(vaultPath);

  if (options.outputFormat !== "markdown") {
    throw new Error(`Unsupported output format: ${options.outputFormat}`);
  }

  const { notes, warnings: scanWarnings } = await scanVault(vaultPath);
  const { filtered, filter } = filterNotes(notes, options.topic);

  if (filtered.length === 0) {
    io.stderr(`No notes matched topic: ${options.topic}\n`);
    return 1;
  }

  const index = createNoteIndex(notes);
  const graph = buildGraph(filtered, index);
  const orderedResult = orderNotes(filtered, graph);

  const config = options.configPath ? await loadConfig(options.configPath) : undefined;
  const defaultLanguage = options.language ?? "zh-TW";
  const plan = buildBookPlan(
    filtered,
    orderedResult.ordered,
    index,
    filter,
    vaultPath,
    options.topic,
    defaultLanguage,
    config
  );

  const warnings: string[] = [...scanWarnings, ...plan.warnings];
  if (orderedResult.hasCycle) {
    warnings.push("Link graph contains cycles; used fallback ordering.");
  }

  if (options.dryRun) {
    io.stdout(renderDryRunSummary(filtered, plan.chapters, warnings));
    return 0;
  }

  const assets: AssetRef[] = [];
  const renderCache = new Map<string, string>();

  const noteRenderer = (note: typeof filtered[number]): string => {
    if (renderCache.has(note.id)) {
      return renderCache.get(note.id) ?? "";
    }
    const rendered = renderNote(note, { vaultPath, index });
    warnings.push(...rendered.warnings);
    assets.push(...rendered.assets);
    renderCache.set(note.id, rendered.markdown);
    return rendered.markdown;
  };

  const title = plan.config.meta?.title ?? "Obsidian Book";
  const bookMarkdown = renderBookMarkdown(plan.chapters, title, noteRenderer);

  const dedupedAssets = dedupeAssets(assets);
  const output = await writeOutput(outputDir, bookMarkdown, plan.config, dedupedAssets);
  warnings.push(...output.warnings);

  if (warnings.length > 0) {
    io.stderr(`Warnings (${warnings.length}):\n- ${warnings.join("\n- ")}\n`);
  }

  io.stdout(`Book generated at ${outputDir}\n`);
  return 0;
}

async function assertDirectory(targetPath: string): Promise<void> {
  const stat = await fs.stat(targetPath).catch(() => null);
  if (!stat || !stat.isDirectory()) {
    throw new Error(`Vault path is not a directory: ${targetPath}`);
  }
}

async function loadConfig(configPath: string): Promise<BookConfig> {
  const resolved = path.resolve(configPath);
  const raw = await fs.readFile(resolved, "utf8");
  const parsed = yaml.parse(raw);
  if (typeof parsed !== "object" || parsed === null) {
    throw new Error(`Invalid config file: ${configPath}`);
  }
  return validateBookConfig(parsed as Record<string, unknown>, configPath);
}

function validateBookConfig(config: Record<string, unknown>, configPath: string): BookConfig {
  const errors: string[] = [];
  const meta = config.meta;
  const source = config.source;
  const structure = config.structure;
  const output = config.output;

  if (meta !== undefined && !isRecord(meta)) {
    errors.push("meta must be an object");
  }
  if (isRecord(meta)) {
    assertOptionalString(meta.title, "meta.title", errors);
    assertOptionalString(meta.author, "meta.author", errors);
    assertOptionalString(meta.language, "meta.language", errors);
  }

  if (source !== undefined && !isRecord(source)) {
    errors.push("source must be an object");
  }
  if (isRecord(source)) {
    assertOptionalString(source.vault, "source.vault", errors);
    assertOptionalString(source.topic, "source.topic", errors);
    assertOptionalStringArray(source.tags, "source.tags", errors);
    assertOptionalStringArray(source.folders, "source.folders", errors);
    assertOptionalStringArray(source.keywords, "source.keywords", errors);
  }

  if (structure !== undefined && !isRecord(structure)) {
    errors.push("structure must be an object");
  }
  if (isRecord(structure)) {
    const chapters = structure.chapters;
    if (chapters !== undefined && !Array.isArray(chapters)) {
      errors.push("structure.chapters must be an array");
    }
    if (Array.isArray(chapters)) {
      chapters.forEach((chapter, index) => {
        if (!isRecord(chapter)) {
          errors.push(`structure.chapters[${index}] must be an object`);
          return;
        }
        assertOptionalString(chapter.title, `structure.chapters[${index}].title`, errors);
        assertOptionalStringArray(chapter.notes, `structure.chapters[${index}].notes`, errors);
        if (chapter.auto !== undefined && typeof chapter.auto !== "boolean") {
          errors.push(`structure.chapters[${index}].auto must be boolean`);
        }
      });
    }
  }

  if (output !== undefined && !isRecord(output)) {
    errors.push("output must be an object");
  }
  if (isRecord(output)) {
    if (output.format !== undefined && output.format !== "markdown") {
      errors.push("output.format must be 'markdown'");
    }
    assertOptionalString(output.cover, "output.cover", errors);
    assertOptionalString(output.template, "output.template", errors);
  }

  if (errors.length > 0) {
    throw new Error(`Invalid config file: ${configPath}. ${errors.join("; ")}`);
  }

  return config as BookConfig;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertOptionalString(value: unknown, label: string, errors: string[]): void {
  if (value !== undefined && typeof value !== "string") {
    errors.push(`${label} must be a string`);
  }
}

function assertOptionalStringArray(value: unknown, label: string, errors: string[]): void {
  if (value === undefined) {
    return;
  }
  if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string")) {
    errors.push(`${label} must be an array of strings`);
  }
}

function renderDryRunSummary(notes: Note[], chapters: { title: string; notes: { title: string; id: string }[] }[], warnings: string[]): string {
  const lines: string[] = [];
  lines.push(`Selected notes: ${notes.length}`);
  lines.push(`Suggested chapters: ${chapters.length}`);
  lines.push("Order:");
  chapters.forEach((chapter, index) => {
    const noteNames = chapter.notes.map((note) => note.title).join(", ");
    lines.push(`${index + 1}. ${chapter.title} (${noteNames})`);
  });
  if (warnings.length > 0) {
    lines.push(`Warnings: ${warnings.length}`);
  }
  return `${lines.join("\n")}\n`;
}

function dedupeAssets(assets: AssetRef[]): AssetRef[] {
  const map = new Map<string, AssetRef>();
  for (const asset of assets) {
    map.set(asset.outputRelativePath, asset);
  }
  return [...map.values()];
}
