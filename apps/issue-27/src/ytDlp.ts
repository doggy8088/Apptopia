import path from "node:path";
import { promises as fs } from "node:fs";
import { randomUUID } from "node:crypto";
import { runCommand } from "./utils/exec";
import { parseDurationToSeconds } from "./utils/duration";

export interface DownloadResult {
  id: string;
  filePath: string;
}

export async function getDurationSeconds(url: string, ytDlpPath: string): Promise<number | null> {
  try {
    const { stdout } = await runCommand(ytDlpPath, ["-J", "--no-playlist", url]);
    const parsed = JSON.parse(stdout);
    const info = Array.isArray(parsed?.entries) ? parsed.entries[0] : parsed;
    if (!info) {
      return null;
    }
    if (typeof info.duration === "number") {
      return info.duration;
    }
    if (typeof info.duration_string === "string") {
      const parsedDuration = parseDurationToSeconds(info.duration_string);
      if (parsedDuration !== null) {
        return parsedDuration;
      }
    }
  } catch {
    // Ignore and try alternate method
  }

  try {
    const { stdout } = await runCommand(ytDlpPath, ["--get-duration", "--no-playlist", url]);
    const line = stdout
      .split("\n")
      .map((value) => value.trim())
      .find((value) => value.length > 0);
    if (!line) {
      return null;
    }
    return parseDurationToSeconds(line);
  } catch {
    return null;
  }
}

export async function downloadVideo(url: string, outputDir: string, ytDlpPath: string): Promise<DownloadResult> {
  const id = randomUUID();
  const outputTemplate = path.join(outputDir, `${id}.%(ext)s`);
  await runCommand(ytDlpPath, [
    "--no-playlist",
    "--merge-output-format",
    "mp4",
    "-o",
    outputTemplate,
    url
  ]);

  const files = await fs.readdir(outputDir);
  const matched = files
    .filter((file) => file.startsWith(id + "."))
    .map((file) => path.join(outputDir, file));
  if (matched.length === 0) {
    throw new Error("下載完成但找不到輸出檔案。");
  }
  matched.sort((a, b) => a.localeCompare(b));
  return { id, filePath: matched[matched.length - 1] };
}
