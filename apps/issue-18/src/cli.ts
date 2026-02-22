#!/usr/bin/env node
import { Command } from "commander";
import { runWithOptions } from "./app";
import { OutputFormat } from "./types";

async function main(): Promise<void> {
  const program = new Command();

  program
    .name("obsidian-book")
    .description("Compile an Obsidian vault into a book-style Markdown manuscript")
    .requiredOption("--vault <path>", "Path to the Obsidian vault")
    .requiredOption("--topic <topic>", "Filter topic (tag:, folder:, keyword: or #tag)")
    .option("--config <path>", "Path to book.yaml configuration")
    .option("--output-dir <path>", "Output directory", "output")
    .option("--output-format <format>", "Output format (markdown)", "markdown")
    .option("--dry-run", "Preview chapter order without writing output", false);

  program.parse(process.argv);

  const opts = program.opts<{
    vault: string;
    topic: string;
    config?: string;
    outputDir: string;
    outputFormat: string;
    dryRun: boolean;
  }>();

  const outputFormat = opts.outputFormat as OutputFormat;
  if (outputFormat !== "markdown") {
    throw new Error("Only markdown output is supported in V1.");
  }

  const exitCode = await runWithOptions({
    vault: opts.vault,
    topic: opts.topic,
    configPath: opts.config,
    outputDir: opts.outputDir,
    outputFormat,
    dryRun: opts.dryRun
  });

  process.exitCode = exitCode;
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`Error: ${message}\n`);
  process.exitCode = 2;
});
