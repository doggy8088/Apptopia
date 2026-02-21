import path from 'path';

export const config = {
  botToken: process.env.TELEGRAM_BOT_TOKEN ?? '',
  dataDir: process.env.DATA_DIR ?? path.join(process.cwd(), 'data'),
  downloadDir: process.env.DOWNLOAD_DIR ?? path.join(process.cwd(), 'downloads'),
  maxDurationSeconds: Number.parseInt(process.env.MAX_DURATION_MINUTES ?? '60', 10) * 60,
  telegramMaxFileSizeBytes:
    Number.parseInt(process.env.TELEGRAM_MAX_FILE_SIZE_MB ?? '50', 10) * 1024 * 1024,
  maxUrlBytes: Number.parseInt(process.env.MAX_URL_BYTES ?? '1000', 10)
};

export function assertConfig(): void {
  if (!config.botToken) {
    throw new Error('Missing TELEGRAM_BOT_TOKEN environment variable.');
  }
}
