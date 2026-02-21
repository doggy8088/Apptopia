import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export async function probeDurationWithFfprobe(filePath: string): Promise<number | null> {
  try {
    const { stdout } = await execFileAsync(
      'ffprobe',
      [
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        filePath
      ],
      { maxBuffer: 1024 * 1024 }
    );
    const value = Number.parseFloat(stdout.trim());
    if (Number.isFinite(value)) {
      return Math.floor(value);
    }
    return null;
  } catch {
    return null;
  }
}
