import path from 'path';
import { promises as fs } from 'fs';

export async function findDownloadedFile(downloadDir: string, jobId: string): Promise<string> {
  const entries = await fs.readdir(downloadDir);
  const fileName = entries.find((entry) => entry.startsWith(`${jobId}.`));
  if (!fileName) {
    throw new Error('找不到下載檔案。');
  }
  return path.join(downloadDir, fileName);
}
