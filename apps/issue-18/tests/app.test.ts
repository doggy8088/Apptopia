import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { runWithOptions } from "../src/app";
import { ReporterIO } from "../src/types";

const vaultPath = path.resolve("tests/fixtures/vault");
const configPath = path.resolve("tests/fixtures/book.yaml");
const badConfigPath = path.resolve("tests/fixtures/bad-book.yaml");

function createCapture(): {
  io: ReporterIO;
  getStdout: () => string;
  getStderr: () => string;
} {
  let stdout = "";
  let stderr = "";

  return {
    io: {
      stdout: (message: string) => {
        stdout += message;
      },
      stderr: (message: string) => {
        stderr += message;
      }
    },
    getStdout: () => stdout,
    getStderr: () => stderr
  };
}

async function createTempDir(): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), "obsidian-book-"));
}

async function readBook(outputDir: string): Promise<string> {
  return fs.readFile(path.join(outputDir, "book.md"), "utf8");
}

describe("obsidian-book-compiler", () => {
  it("filters notes by tag and generates book markdown", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    const exitCode = await runWithOptions(
      {
        vault: vaultPath,
        topic: "#python",
        outputDir,
        outputFormat: "markdown",
        dryRun: false
      },
      capture.io
    );

    expect(exitCode).toBe(0);

    const book = await readBook(outputDir);
    expect(book).toContain("Note One");
    expect(book).toContain("Note Three");
  });

  it("filters notes by folder", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    await runWithOptions(
      {
        vault: vaultPath,
        topic: "folder:Guides",
        outputDir,
        outputFormat: "markdown",
        dryRun: false
      },
      capture.io
    );

    const book = await readBook(outputDir);
    expect(book).toContain("Note Two");
    expect(book).not.toContain("Note One");
  });

  it("converts wikilinks, callouts, and embeds assets", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    await runWithOptions(
      {
        vault: vaultPath,
        topic: "#python",
        outputDir,
        outputFormat: "markdown",
        dryRun: false
      },
      capture.io
    );

    const book = await readBook(outputDir);
    expect(book).toContain("[Second](#note-two)");
    expect(book).toContain("**📝 Note: Remember**");
    expect(book).toContain("![image](./assets/image.png)");

    const assetPath = path.join(outputDir, "assets", "image.png");
    const assetStat = await fs.stat(assetPath);
    expect(assetStat.isFile()).toBe(true);
  });

  it("uses book.yaml chapter order when provided", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    await runWithOptions(
      {
        vault: vaultPath,
        topic: "keyword:kubernetes",
        configPath,
        outputDir,
        outputFormat: "markdown",
        dryRun: false
      },
      capture.io
    );

    const book = await readBook(outputDir);
    const introIndex = book.indexOf("## Intro");
    const noteThreeIndex = book.indexOf("Note Three");
    expect(introIndex).toBeGreaterThan(-1);
    expect(introIndex).toBeLessThan(noteThreeIndex);
  });

  it("rejects invalid book.yaml", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    await expect(
      runWithOptions(
        {
          vault: vaultPath,
          topic: "keyword:kubernetes",
          configPath: badConfigPath,
          outputDir,
          outputFormat: "markdown",
          dryRun: false
        },
        capture.io
      )
    ).rejects.toThrow("Invalid config file");
  });

  it("skips unsafe embedded asset paths", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    await runWithOptions(
      {
        vault: vaultPath,
        topic: "#python",
        outputDir,
        outputFormat: "markdown",
        dryRun: false
      },
      capture.io
    );

    const book = await readBook(outputDir);
    expect(book).toContain("Skipped unsafe asset");
    expect(capture.getStderr()).toContain("Skipped unsafe asset path: ../outside.png");
  });

  it("supports dry-run preview", async () => {
    const outputDir = await createTempDir();
    const capture = createCapture();

    const exitCode = await runWithOptions(
      {
        vault: vaultPath,
        topic: "keyword:kubernetes",
        outputDir,
        outputFormat: "markdown",
        dryRun: true
      },
      capture.io
    );

    expect(exitCode).toBe(0);
    expect(capture.getStdout()).toContain("Suggested chapters");
  });
});
