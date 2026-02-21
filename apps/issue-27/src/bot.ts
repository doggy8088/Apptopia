import TelegramBot from 'node-telegram-bot-api';
import path from 'path';
import crypto from 'crypto';
import { config, assertConfig } from './config';
import {
  appendConversationLog,
  appendDownloadLog,
  ensureStorageReady,
  loadQueueState,
  saveQueueState,
  upsertUserSettings,
  QueueStateItem
} from './storage';
import { DownloadQueue } from './queue';
import { extractUrl, validateUrl } from './utils/validation';
import { fetchMetadata, downloadVideo } from './yt-dlp';
import { findDownloadedFile } from './utils/downloads';
import { getFileSizeBytes, isFileSizeAllowed, safeUnlink } from './utils/files';
import { probeDurationWithFfprobe } from './utils/ffprobe';

const MAX_QUEUE_HISTORY = 200;
const maxDurationMinutes = Math.floor(config.maxDurationSeconds / 60);

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;
  return `${minutes}m ${remainSeconds}s`;
}

async function main(): Promise<void> {
  assertConfig();
  await ensureStorageReady();

  const bot = new TelegramBot(config.botToken, { polling: true });

  const previousQueue = await loadQueueState();
  const now = new Date().toISOString();
  const restoredQueue: QueueStateItem[] = previousQueue.map((item): QueueStateItem => {
    if (item.status === 'queued' || item.status === 'processing') {
      return { ...item, status: 'queued', updatedAt: now };
    }
    return item;
  });

  const queue = new DownloadQueue(
    restoredQueue,
    async (item) => {
      const chatId = item.chatId;
      const url = item.url;
      const userId = item.userId;

      await bot.sendMessage(chatId, '開始處理下載，請稍候...');

      let metadata;
      try {
        metadata = await fetchMetadata(url);
      } catch (error) {
        const err = error as Error;
        await bot.sendMessage(chatId, err.message);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: err.message
        });
        return;
      }

      const title = metadata.title ?? 'Video';
      const durationSeconds =
        typeof metadata.duration === 'number' && Number.isFinite(metadata.duration)
          ? Math.floor(metadata.duration)
          : null;

      if (durationSeconds && durationSeconds > config.maxDurationSeconds) {
        const message = `影片長度 ${formatDuration(
          durationSeconds
        )} 超過限制（${maxDurationMinutes} 分鐘）。`;
        await bot.sendMessage(chatId, message);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: message,
          title,
          durationSeconds
        });
        return;
      }

      const outputTemplate = path.join(config.downloadDir, `${item.id}.%(ext)s`);

      try {
        await downloadVideo(url, outputTemplate);
      } catch (error) {
        const err = error as Error;
        await bot.sendMessage(chatId, err.message);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: err.message,
          title,
          durationSeconds: durationSeconds ?? undefined
        });
        return;
      }

      let downloadedFile: string;
      try {
        downloadedFile = await findDownloadedFile(config.downloadDir, item.id);
      } catch (error) {
        const err = error as Error;
        await bot.sendMessage(chatId, err.message);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: err.message,
          title,
          durationSeconds: durationSeconds ?? undefined
        });
        return;
      }

      let finalDuration = durationSeconds;
      if (!finalDuration) {
        finalDuration = await probeDurationWithFfprobe(downloadedFile);
        if (!finalDuration) {
          const message = '無法取得影片長度，請確認影片可被辨識。';
          await bot.sendMessage(chatId, message);
          await appendDownloadLog({
            timestamp: new Date().toISOString(),
            chatId,
            userId,
            url,
            status: 'error',
            errorMessage: message,
            title
          });
          await safeUnlink(downloadedFile);
          return;
        }
        if (finalDuration > config.maxDurationSeconds) {
          const message = `影片長度 ${formatDuration(
            finalDuration
          )} 超過限制（${maxDurationMinutes} 分鐘）。`;
          await bot.sendMessage(chatId, message);
          await appendDownloadLog({
            timestamp: new Date().toISOString(),
            chatId,
            userId,
            url,
            status: 'error',
            errorMessage: message,
            title,
            durationSeconds: finalDuration
          });
          await safeUnlink(downloadedFile);
          return;
        }
      }

      const fileSizeBytes = await getFileSizeBytes(downloadedFile);
      if (!isFileSizeAllowed(fileSizeBytes, config.telegramMaxFileSizeBytes)) {
        const message = `檔案大小 ${formatBytes(fileSizeBytes)} 超過 Telegram Bot 限制（${formatBytes(
          config.telegramMaxFileSizeBytes
        )}）。`;
        await bot.sendMessage(chatId, message);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: message,
          title,
          durationSeconds: finalDuration ?? undefined,
          fileSizeBytes
        });
        await safeUnlink(downloadedFile);
        return;
      }

      try {
        await bot.sendVideo(chatId, downloadedFile, {
          caption: title
        });
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'success',
          title,
          durationSeconds: finalDuration ?? undefined,
          fileSizeBytes
        });
      } catch (error) {
        const err = error as Error;
        await bot.sendMessage(chatId, `回傳影片失敗：${err.message}`);
        await appendDownloadLog({
          timestamp: new Date().toISOString(),
          chatId,
          userId,
          url,
          status: 'error',
          errorMessage: err.message,
          title,
          durationSeconds: finalDuration ?? undefined,
          fileSizeBytes
        });
      } finally {
        await safeUnlink(downloadedFile);
      }
    },
    async (items) => {
      const snapshot = items.slice(-MAX_QUEUE_HISTORY);
      await saveQueueState(snapshot);
    }
  );

  bot.onText(/\/(start|help)/, async (msg) => {
    await bot.sendMessage(
      msg.chat.id,
      '請傳入影片網址（支援 yt-dlp 支援的站點）。\n' +
        `限制：${maxDurationMinutes} 分鐘內、檔案大小需小於 Telegram Bot 上限。`
    );
  });

  bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from?.id;
    const username = msg.from?.username;
    const text = msg.text;

    await appendConversationLog({
      timestamp: new Date().toISOString(),
      chatId,
      userId,
      username,
      text
    });

    if (userId) {
      await upsertUserSettings(userId);
    }

    if (!text || text.startsWith('/')) {
      return;
    }

    const url = extractUrl(text);
    if (!url) {
      await bot.sendMessage(chatId, '請提供影片網址。');
      return;
    }

    const validation = validateUrl(url, config.maxUrlBytes);
    if (!validation.ok) {
      await bot.sendMessage(chatId, validation.reason);
      return;
    }

    const now = new Date().toISOString();
    const item: QueueStateItem = {
      id: crypto.randomUUID(),
      chatId,
      userId,
      messageId: msg.message_id,
      url: validation.url,
      status: 'queued',
      createdAt: now,
      updatedAt: now
    };

    const position = queue.enqueue(item);
    const ahead = position - 1;
    if (ahead > 0) {
      await bot.sendMessage(chatId, `已加入隊列，前方尚有 ${ahead} 部影片。`);
    } else {
      await bot.sendMessage(chatId, '已加入隊列，稍後開始處理。');
    }
  });

  bot.on('polling_error', (error) => {
    console.error('Polling error:', error.message);
  });
}

void main();
