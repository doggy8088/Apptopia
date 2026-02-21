import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export interface YtDlpMetadata {
  title?: string;
  duration?: number;
  webpage_url?: string;
}

export async function fetchMetadata(url: string): Promise<YtDlpMetadata> {
  try {
    const { stdout } = await execFileAsync('yt-dlp', ['--dump-single-json', '--no-playlist', url], {
      maxBuffer: 1024 * 1024 * 10
    });
    return JSON.parse(stdout) as YtDlpMetadata;
  } catch (error) {
    const err = error as Error;
    throw new Error(`無法取得影片資訊：${err.message}`);
  }
}

export async function downloadVideo(url: string, outputTemplate: string): Promise<void> {
  try {
    await execFileAsync(
      'yt-dlp',
      [
        '--no-playlist',
        '-f',
        'mp4/best[ext=mp4]/best',
        '-o',
        outputTemplate,
        url
      ],
      { maxBuffer: 1024 * 1024 * 10 }
    );
  } catch (error) {
    const err = error as Error;
    throw new Error(`下載失敗：${err.message}`);
  }
}
