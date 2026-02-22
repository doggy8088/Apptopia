import { runCommand } from "./utils/exec";

export async function probeDurationSeconds(filePath: string): Promise<number | null> {
  try {
    const { stdout } = await runCommand("ffprobe", [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=noprint_wrappers=1:nokey=1",
      filePath
    ]);
    const value = Number.parseFloat(stdout.trim());
    if (Number.isNaN(value)) {
      return null;
    }
    return Math.floor(value);
  } catch {
    return null;
  }
}
