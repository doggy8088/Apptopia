import TelegramBot from "node-telegram-bot-api";
import path from "node:path";
import { promises as fs } from "node:fs";
import { randomUUID } from "node:crypto";
import { DataStore } from "./storage/dataStore";
import { JobQueue } from "./queue/jobQueue";
import type { QueueItem, ConversationEntry, DownloadRecord } from "./types";
import { extractFirstUrl, validateUrlInput } from "./utils/url";
import { formatDuration } from "./utils/duration";
import { MAX_DURATION_SECONDS, TELEGRAM_MAX_FILE_BYTES } from "./constants";
import { isDurationAllowed, isFileSizeAllowed } from "./limits";
import { downloadVideo, getDurationSeconds } from "./ytDlp";
import { probeDurationSeconds } from "./ffprobe";

export interface BotConfig {
  token: string;
  dataDir: string;
  ytDlpPath: string;
}

const MAX_DURATION_TEXT = formatDuration(MAX_DURATION_SECONDS);

export async function runBot(config: BotConfig): Promise<void> {
  const store = new DataStore(config.dataDir);
  await store.ensure();

  const bot = new TelegramBot(config.token, { polling: true });
  const queueItems = await store.loadQueue();
  const queue = new JobQueue(queueItems, (items) => store.saveQueue(items), (item) =>
    processQueueItem(item, bot, store, config)
  );

  bot.on("message", async (message) => {
    const chatId = message.chat.id.toString();
    const userId = message.from?.id?.toString() ?? "unknown";
    const username = message.from?.username ?? message.from?.first_name;
    const text = message.text ?? "";
    await store.upsertUserSettings(chatId);
    await store.appendConversation(
      buildConversationEntry({
        chatId,
        userId,
        username,
        messageId: message.message_id,
        direction: "in",
        text,
        payloadType: "text"
      })
    );

    if (text.startsWith("/start") || text.startsWith("/help")) {
      await sendMessageLogged(bot, store, chatId, userId, helpMessage());
      return;
    }

    const urlCandidate = extractFirstUrl(text);
    if (!urlCandidate) {
      await sendMessageLogged(bot, store, chatId, userId, "請傳送影片網址，或輸入 /help 查看說明。");
      return;
    }

    const validation = validateUrlInput(urlCandidate);
    if (!validation.ok || !validation.url) {
      await sendMessageLogged(bot, store, chatId, userId, validation.error ?? "網址無效。");
      return;
    }

    const now = new Date().toISOString();
    const queueItem: QueueItem = {
      id: randomUUID(),
      chatId,
      userId,
      url: validation.url,
      status: "queued",
      createdAt: now,
      updatedAt: now
    };

    await queue.enqueue(queueItem);
    const position = queue.getPosition(queueItem.id);
    const positionText = position ? `目前排隊位置：第 ${position} 位。` : "已加入佇列。";
    await sendMessageLogged(
      bot,
      store,
      chatId,
      userId,
      `已收到網址，正在排隊下載。${positionText}`
    );
  });
}

function helpMessage(): string {
  return [
    "請直接傳送影片網址，我會使用 yt-dlp 下載並回傳影片。",
    `限制：影片長度不可超過 ${MAX_DURATION_TEXT}，檔案大小不可超過 ${formatFileSize(TELEGRAM_MAX_FILE_BYTES)}。`,
    "若超過限制會直接回覆錯誤。",
    "注意：伺服器需預先安裝 yt-dlp。"
  ].join("\n");
}

async function processQueueItem(
  item: QueueItem,
  bot: TelegramBot,
  store: DataStore,
  config: BotConfig
): Promise<void> {
  const startedAt = new Date().toISOString();
  try {
    let durationSeconds: number | null = await getDurationSeconds(item.url, config.ytDlpPath);
    if (durationSeconds !== null && !isDurationAllowed(durationSeconds)) {
      await sendMessageLogged(
        bot,
        store,
        item.chatId,
        item.userId,
        `影片長度 ${formatDuration(durationSeconds)} 超過限制 ${MAX_DURATION_TEXT}，已取消下載。`
      );
      await store.appendDownload({
        id: item.id,
        url: item.url,
        chatId: item.chatId,
        userId: item.userId,
        status: "rejected_duration",
        durationSeconds,
        createdAt: startedAt,
        completedAt: new Date().toISOString()
      });
      return;
    }

    const outputDir = path.join(config.dataDir, "downloads");
    const download = await downloadVideo(item.url, outputDir, config.ytDlpPath);
    const stats = await fs.stat(download.filePath);

    if (!isFileSizeAllowed(stats.size)) {
      await sendMessageLogged(
        bot,
        store,
        item.chatId,
        item.userId,
        `檔案大小 ${formatFileSize(stats.size)} 超過 Telegram 上限 ${formatFileSize(
          TELEGRAM_MAX_FILE_BYTES
        )}，已取消回傳。`
      );
      await store.appendDownload({
        id: item.id,
        url: item.url,
        chatId: item.chatId,
        userId: item.userId,
        status: "rejected_size",
        durationSeconds: durationSeconds ?? undefined,
        filePath: download.filePath,
        fileSizeBytes: stats.size,
        createdAt: startedAt,
        completedAt: new Date().toISOString()
      });
      return;
    }

    if (durationSeconds === null) {
      durationSeconds = await probeDurationSeconds(download.filePath);
      if (durationSeconds === null) {
        await sendMessageLogged(
          bot,
          store,
          item.chatId,
          item.userId,
          "無法判斷影片長度（缺少 ffprobe 或解析失敗），因此取消回傳。"
        );
        await store.appendDownload({
          id: item.id,
          url: item.url,
          chatId: item.chatId,
          userId: item.userId,
          status: "error",
          filePath: download.filePath,
          fileSizeBytes: stats.size,
          createdAt: startedAt,
          completedAt: new Date().toISOString(),
          error: "Unable to determine duration"
        });
        return;
      }
      if (!isDurationAllowed(durationSeconds)) {
        await sendMessageLogged(
          bot,
          store,
          item.chatId,
          item.userId,
          `影片長度 ${formatDuration(durationSeconds)} 超過限制 ${MAX_DURATION_TEXT}，已取消下載。`
        );
        await store.appendDownload({
          id: item.id,
          url: item.url,
          chatId: item.chatId,
          userId: item.userId,
          status: "rejected_duration",
          durationSeconds,
          filePath: download.filePath,
          fileSizeBytes: stats.size,
          createdAt: startedAt,
          completedAt: new Date().toISOString()
        });
        return;
      }
    }

    const caption = `下載完成！長度 ${formatDuration(durationSeconds ?? 0)}，大小 ${formatFileSize(stats.size)}。`;
    await sendVideoLogged(bot, store, item.chatId, item.userId, download.filePath, caption);
    await store.appendDownload({
      id: item.id,
      url: item.url,
      chatId: item.chatId,
      userId: item.userId,
      status: "sent",
      durationSeconds: durationSeconds ?? undefined,
      filePath: download.filePath,
      fileSizeBytes: stats.size,
      createdAt: startedAt,
      completedAt: new Date().toISOString()
    });
  } catch (error: any) {
    const message = error?.message ?? "下載失敗";
    await sendMessageLogged(bot, store, item.chatId, item.userId, `下載失敗：${message}`);
    await store.appendDownload({
      id: item.id,
      url: item.url,
      chatId: item.chatId,
      userId: item.userId,
      status: "error",
      createdAt: startedAt,
      completedAt: new Date().toISOString(),
      error: message
    });
    throw error;
  }
}

function buildConversationEntry(entry: Omit<ConversationEntry, "id" | "timestamp">): ConversationEntry {
  return {
    id: randomUUID(),
    timestamp: new Date().toISOString(),
    ...entry
  };
}

async function sendMessageLogged(
  bot: TelegramBot,
  store: DataStore,
  chatId: string,
  userId: string,
  text: string
): Promise<void> {
  const response = await bot.sendMessage(chatId, text);
  await store.appendConversation(
    buildConversationEntry({
      chatId,
      userId,
      messageId: response.message_id,
      direction: "out",
      text,
      payloadType: "text"
    })
  );
}

async function sendVideoLogged(
  bot: TelegramBot,
  store: DataStore,
  chatId: string,
  userId: string,
  filePath: string,
  caption: string
): Promise<void> {
  const response = await bot.sendVideo(chatId, filePath, { caption });
  await store.appendConversation(
    buildConversationEntry({
      chatId,
      userId,
      messageId: response.message_id,
      direction: "out",
      text: caption,
      payloadType: "video"
    })
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}
