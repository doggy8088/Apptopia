import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { AssetRef, BookConfig } from "./types";

export interface OutputResult {
  warnings: string[];
}

export async function writeOutput(
  outputDir: string,
  bookMarkdown: string,
  config: BookConfig,
  assets: AssetRef[]
): Promise<OutputResult> {
  const warnings: string[] = [];
  await fs.mkdir(outputDir, { recursive: true });

  const bookPath = path.join(outputDir, "book.md");
  await fs.writeFile(bookPath, bookMarkdown, "utf8");

  const configPath = path.join(outputDir, "book.yaml");
  const yamlContent = yaml.stringify(config);
  await fs.writeFile(configPath, yamlContent, "utf8");

  const assetRoot = path.join(outputDir, "assets");
  for (const asset of assets) {
    const destination = path.join(outputDir, asset.outputRelativePath);
    try {
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.copyFile(asset.sourcePath, destination);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      warnings.push(`Failed to copy asset ${asset.sourcePath}: ${message}`);
    }
  }

  return { warnings };
}
