import { promises as fs } from 'fs';

export async function fileExists(path: string): Promise<boolean> {
  try {
    await fs.access(path);
    return true;
  } catch {
    return false;
  }
}

export async function ensureDir(path: string): Promise<void> {
  await fs.mkdir(path, { recursive: true });
}

export async function getFileSizeBytes(path: string): Promise<number> {
  const stats = await fs.stat(path);
  return stats.size;
}

export function isFileSizeAllowed(sizeBytes: number, maxBytes: number): boolean {
  return sizeBytes <= maxBytes;
}

export async function safeUnlink(path: string): Promise<void> {
  try {
    await fs.unlink(path);
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err.code !== 'ENOENT') {
      throw error;
    }
  }
}

export async function writeJsonFile<T>(path: string, data: T): Promise<void> {
  const tempPath = `${path}.tmp`;
  await fs.writeFile(tempPath, JSON.stringify(data, null, 2), 'utf8');
  await fs.rename(tempPath, path);
}
