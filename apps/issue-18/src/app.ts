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
  const plan = buildBookPlan(filtered, orderedResult.ordered, index, filter, vaultPath, options.topic, config);

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
  return parsed as BookConfig;
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
