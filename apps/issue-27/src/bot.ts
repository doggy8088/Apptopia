import TelegramBot from "node-telegram-bot-api";
import path from "node:path";
import * as https from "node:https";
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
import {
  buildAzureBlobObjectName,
  describeAzureBlobUploadFailure,
  uploadFileToAzureBlobContainer
} from "./azureBlob";

export interface BotConfig {
  token: string;
  dataDir: string;
  ytDlpPath: string;
  azureBlobContainerSasUrl?: string;
}

const MAX_DURATION_TEXT = formatDuration(MAX_DURATION_SECONDS);
const TELEGRAM_SEND_VIDEO_RETRY_DELAYS_MS = [5000, 15000, 30000] as const;
const TELEGRAM_REQUEST_TIMEOUT_MS = 10 * 60 * 1000;
const TELEGRAM_HTTP_KEEP_ALIVE_AGENT = new https.Agent({
  keepAlive: true,
  keepAliveMsecs: 10_000,
  maxSockets: 20,
  maxFreeSockets: 10
});
let progressMessageReporter: ProgressMessageReporter | null = null;

export async function runBot(config: BotConfig): Promise<void> {
  logInfo("bot.starting", {
    dataDir: config.dataDir,
    ytDlpPath: config.ytDlpPath
  });
  const store = new DataStore(config.dataDir);
  await store.ensure();
  logInfo("bot.store_ready", { dataDir: config.dataDir });

  const requestOptions = {
    agentClass: https.Agent,
    agentOptions: {
      keepAlive: true,
      keepAliveMsecs: 10_000,
      maxSockets: 20,
      maxFreeSockets: 10
    },
    agent: TELEGRAM_HTTP_KEEP_ALIVE_AGENT,
    timeout: TELEGRAM_REQUEST_TIMEOUT_MS
  } as any;

  const bot = new TelegramBot(config.token, {
    polling: true,
    request: requestOptions
  });
  progressMessageReporter = new ProgressMessageReporter(bot);
  logInfo("telegram.request_keepalive_enabled", {
    keepAlive: true,
    keepAliveMsecs: 10_000,
    maxSockets: 20,
    maxFreeSockets: 10,
    requestTimeoutMs: TELEGRAM_REQUEST_TIMEOUT_MS
  });
  bot.on("polling_error", (error) => {
    const pollingError = error as any;
    logError("telegram.polling_error", {
      code: pollingError?.code,
      error: pollingError?.message ?? String(error)
    });
  });
  const queueItems = await store.loadQueue();
  logInfo("bot.queue_loaded", { count: queueItems.length });
  const queue = new JobQueue(queueItems, (items) => store.saveQueue(items), (item) =>
    processQueueItem(item, bot, store, config)
  );
  await notifyKnownUsersServerStarted(bot, store);

  bot.on("message", async (message) => {
    const chatId = message.chat.id.toString();
    const userId = message.from?.id?.toString() ?? "unknown";
    const username = message.from?.username ?? message.from?.first_name;
    const text = message.text ?? "";
    const messageId = message.message_id;
    let replied = false;

    const reply = async (replyText: string): Promise<TelegramBot.Message> => {
      const response = await sendMessageLogged(bot, store, chatId, userId, replyText);
      replied = true;
      return response;
    };

    try {
      logInfo("message.received", {
        chatId,
        userId,
        messageId,
        hasText: Boolean(message.text),
        textLength: text.length,
        preview: previewText(text)
      });

      await safeUpsertUserSettings(store, chatId);
      await safeAppendConversation(
        store,
        buildConversationEntry({
          chatId,
          userId,
          username,
          messageId,
          direction: "in",
          text,
          payloadType: "text"
        }),
        "message.inbound_log_failed"
      );

      if (text.startsWith("/start") || text.startsWith("/help")) {
        logInfo("message.command_help", { chatId, userId, messageId });
        await reply(helpMessage());
        return;
      }

      const urlCandidate = extractFirstUrl(text);
      if (!urlCandidate) {
        logInfo("message.no_url_found", { chatId, userId, messageId });
        await reply("請傳送影片網址，或輸入 /help 查看說明。");
        return;
      }

      logInfo("message.url_candidate_found", {
        chatId,
        userId,
        messageId,
        urlCandidate
      });
      const validation = await validateUrlInput(urlCandidate);
      if (!validation.ok || !validation.url) {
        logWarn("message.url_invalid", {
          chatId,
          userId,
          messageId,
          urlCandidate,
          error: validation.error ?? "網址無效。"
        });
        await reply(validation.error ?? "網址無效。");
        return;
      }

      logInfo("message.url_validated", {
        chatId,
        userId,
        messageId,
        url: validation.url
      });
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

      const progressMessage = await reply("已收到網址，正在排隊下載。已加入佇列。");
      progressMessageReporter?.register({
        queueItemId: queueItem.id,
        chatId,
        messageId: progressMessage.message_id,
        url: queueItem.url,
        initialStatus: "已收到網址，正在排隊下載。已加入佇列。"
      });

      logInfo("queue.enqueue_request", {
        queueItemId: queueItem.id,
        chatId,
        userId,
        url: queueItem.url
      });
      await queue.enqueue(queueItem);
      const position = queue.getPosition(queueItem.id);
      logInfo("queue.enqueued", {
        queueItemId: queueItem.id,
        chatId,
        userId,
        position
      });
    } catch (error: any) {
      logError("message.handler_failed", {
        chatId,
        userId,
        messageId,
        replied,
        error: error?.message ?? String(error)
      });
      if (!replied) {
        try {
          await bot.sendMessage(chatId, "處理訊息時發生錯誤，請稍後再試。");
          replied = true;
        } catch (sendError: any) {
          logError("message.fallback_reply_failed", {
            chatId,
            userId,
            messageId,
            error: sendError?.message ?? String(sendError)
          });
        }
      }
    }
  });

  logInfo("bot.polling_started");
}

async function notifyKnownUsersServerStarted(bot: TelegramBot, store: DataStore): Promise<void> {
  let chatIds: string[] = [];
  try {
    chatIds = await store.listKnownChatIds();
    logInfo("startup_notify.targets_loaded", { count: chatIds.length });
  } catch (error: any) {
    logWarn("startup_notify.targets_load_failed", {
      error: error?.message ?? String(error)
    });
    return;
  }

  if (chatIds.length === 0) {
    logInfo("startup_notify.no_targets");
    return;
  }

  const text = "伺服器已開啟，可以開始傳送影片網址。";
  let successCount = 0;
  let failureCount = 0;

  for (const chatId of chatIds) {
    try {
      logInfo("startup_notify.send.start", { chatId });
      await sendMessageLogged(bot, store, chatId, "system", text);
      successCount += 1;
      logInfo("startup_notify.send.done", { chatId });
    } catch (error: any) {
      failureCount += 1;
      logWarn("startup_notify.send.failed", {
        chatId,
        error: error?.message ?? String(error)
      });
    }
  }

  logInfo("startup_notify.completed", {
    total: chatIds.length,
    successCount,
    failureCount
  });
}

function helpMessage(): string {
  return [
    "請直接傳送影片網址，我會使用 yt-dlp 下載並回傳影片。",
    `限制：影片長度不可超過 ${MAX_DURATION_TEXT}，檔案大小不可超過 ${formatFileSize(TELEGRAM_MAX_FILE_BYTES)}。`,
    "若超過限制會回覆錯誤；若已設定 Azure Blob SAS，超過 Telegram 大小上限時會改回傳下載連結。",
    "為了安全，會拒絕本機或內網網址。",
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
  let downloadPath: string | null = null;
  let durationSeconds: number | null = null;
  let fileSizeBytes: number | undefined;
  let shouldDeleteDownloadedFile = true;
  logInfo("queue_item.start", {
    queueItemId: item.id,
    chatId: item.chatId,
    userId: item.userId,
    url: item.url
  });
  try {
    logInfo("queue_item.duration_check.start", { queueItemId: item.id });
    durationSeconds = await getDurationSeconds(item.url, config.ytDlpPath);
    logInfo("queue_item.duration_check.done", {
      queueItemId: item.id,
      durationSeconds
    });
    if (durationSeconds !== null && !isDurationAllowed(durationSeconds)) {
      logWarn("queue_item.rejected_duration_pre_download", {
        queueItemId: item.id,
        durationSeconds
      });
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
    logInfo("queue_item.download.start", { queueItemId: item.id, outputDir });
    const download = await downloadVideo(item.url, outputDir, config.ytDlpPath);
    downloadPath = download.filePath;
    logInfo("queue_item.download.done", {
      queueItemId: item.id,
      downloadId: download.id,
      filePath: download.filePath
    });
    const stats = await fs.stat(download.filePath);
    fileSizeBytes = stats.size;
    logInfo("queue_item.file_stat", {
      queueItemId: item.id,
      bytes: stats.size
    });

    if (!isFileSizeAllowed(stats.size)) {
      if (!config.azureBlobContainerSasUrl) {
        logWarn("queue_item.rejected_size", {
          queueItemId: item.id,
          bytes: stats.size
        });
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
          filePath: downloadPath,
          fileSizeBytes: stats.size,
          createdAt: startedAt,
          completedAt: new Date().toISOString()
        });
        return;
      }

      logInfo("queue_item.azure_upload.start", {
        queueItemId: item.id,
        bytes: stats.size
      });
      try {
        const blobName = buildAzureBlobObjectName(download.filePath, `telegram-bot/${item.chatId}/${item.id}`);
        const uploadResult = await uploadFileToAzureBlobContainer({
          containerSasUrl: config.azureBlobContainerSasUrl,
          filePath: download.filePath,
          blobName
        });
        logInfo("queue_item.azure_upload.done", {
          queueItemId: item.id,
          bytes: stats.size,
          blobName: uploadResult.blobName,
          blobUrl: uploadResult.blobUrl
        });
        await sendMessageLogged(
          bot,
          store,
          item.chatId,
          item.userId,
          [
            `檔案大小 ${formatFileSize(stats.size)} 超過 Telegram 上限 ${formatFileSize(
              TELEGRAM_MAX_FILE_BYTES
            )}，已改為上傳到 Azure Blob。`,
            `下載連結：${uploadResult.accessUrl}`,
            "注意：此連結對應檔案會依 Azure Storage 生命週期規則自動刪除（目前設定為 7 天）。"
          ].join("\n")
        );
        await store.appendDownload({
          id: item.id,
          url: item.url,
          chatId: item.chatId,
          userId: item.userId,
          status: "uploaded_blob",
          durationSeconds: durationSeconds ?? undefined,
          filePath: downloadPath,
          fileSizeBytes: stats.size,
          createdAt: startedAt,
          completedAt: new Date().toISOString()
        });
        logInfo("queue_item.recorded_blob_upload", {
          queueItemId: item.id,
          blobName: uploadResult.blobName,
          blobUrl: uploadResult.blobUrl
        });
      } catch (azureUploadError: any) {
        const reason = describeAzureBlobUploadFailure(azureUploadError);
        logWarn("queue_item.azure_upload.failed", {
          queueItemId: item.id,
          bytes: stats.size,
          error: reason
        });
        await sendMessageLogged(
          bot,
          store,
          item.chatId,
          item.userId,
          [
            `檔案大小 ${formatFileSize(stats.size)} 超過 Telegram 上限 ${formatFileSize(
              TELEGRAM_MAX_FILE_BYTES
            )}。`,
            `已嘗試改上傳到 Azure Blob，但失敗了：${reason}`
          ].join("\n")
        );
        await store.appendDownload({
          id: item.id,
          url: item.url,
          chatId: item.chatId,
          userId: item.userId,
          status: "error_blob_upload",
          durationSeconds: durationSeconds ?? undefined,
          filePath: downloadPath,
          fileSizeBytes: stats.size,
          createdAt: startedAt,
          completedAt: new Date().toISOString(),
          error: reason
        });
      }
      return;
    }

    if (durationSeconds === null) {
      logInfo("queue_item.ffprobe_duration.start", { queueItemId: item.id, filePath: download.filePath });
      durationSeconds = await probeDurationSeconds(download.filePath);
      logInfo("queue_item.ffprobe_duration.done", { queueItemId: item.id, durationSeconds });
      if (durationSeconds === null) {
        logWarn("queue_item.duration_unknown", { queueItemId: item.id });
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
        filePath: downloadPath,
        fileSizeBytes: stats.size,
        createdAt: startedAt,
        completedAt: new Date().toISOString(),
          error: "Unable to determine duration"
        });
        return;
      }
      if (!isDurationAllowed(durationSeconds)) {
        logWarn("queue_item.rejected_duration_post_download", {
          queueItemId: item.id,
          durationSeconds
        });
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
        filePath: downloadPath,
        fileSizeBytes: stats.size,
        createdAt: startedAt,
        completedAt: new Date().toISOString()
        });
        return;
      }
    }

    const caption = `下載完成！長度 ${formatDuration(durationSeconds ?? 0)}，大小 ${formatFileSize(stats.size)}。`;
    logInfo("queue_item.send_video.start", {
      queueItemId: item.id,
      filePath: download.filePath,
      bytes: stats.size,
      durationSeconds
    });
    await sendVideoWithRetry({
      bot,
      store,
      queueItemId: item.id,
      chatId: item.chatId,
      userId: item.userId,
      filePath: download.filePath,
      caption
    });
    logInfo("queue_item.send_video.done", { queueItemId: item.id });
    await store.appendDownload({
      id: item.id,
      url: item.url,
      chatId: item.chatId,
      userId: item.userId,
      status: "sent",
      durationSeconds: durationSeconds ?? undefined,
      filePath: downloadPath,
      fileSizeBytes: stats.size,
      createdAt: startedAt,
      completedAt: new Date().toISOString()
    });
    logInfo("queue_item.recorded_sent", { queueItemId: item.id });
  } catch (error: any) {
    const message = error?.message ?? "下載失敗";
    const isRetryableUploadFailure = Boolean((error as any)?.isRetryableTelegramUploadFailure);
    if (isRetryableUploadFailure && downloadPath) {
      shouldDeleteDownloadedFile = false;
      logWarn("queue_item.cleanup_preserved_for_retry", {
        queueItemId: item.id,
        downloadPath
      });
    }
    logError("queue_item.failed", {
      queueItemId: item.id,
      error: message
    });
    try {
      await sendMessageLogged(bot, store, item.chatId, item.userId, `下載失敗：${message}`);
    } catch (noticeError: any) {
      logWarn("queue_item.failure_notice_failed", {
        queueItemId: item.id,
        error: noticeError?.message ?? String(noticeError)
      });
    }
    try {
      await store.appendDownload({
        id: item.id,
        url: item.url,
        chatId: item.chatId,
        userId: item.userId,
        status: isRetryableUploadFailure ? "error_send_retryable" : "error",
        durationSeconds: durationSeconds ?? undefined,
        filePath: downloadPath ?? undefined,
        fileSizeBytes,
        createdAt: startedAt,
        completedAt: new Date().toISOString(),
        error: message
      });
    } catch (recordError: any) {
      logWarn("queue_item.failure_record_failed", {
        queueItemId: item.id,
        error: recordError?.message ?? String(recordError)
      });
    }
    throw error;
  } finally {
    logInfo("queue_item.cleanup", {
      queueItemId: item.id,
      downloadPath,
      willDelete: shouldDeleteDownloadedFile
    });
    if (shouldDeleteDownloadedFile) {
      await safeUnlink(downloadPath);
    }
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
): Promise<TelegramBot.Message> {
  logInfo("telegram.send_message.start", {
    chatId,
    userId,
    textLength: text.length,
    preview: previewText(text)
  });
  const response = await bot.sendMessage(chatId, text);
  logInfo("telegram.send_message.done", {
    chatId,
    userId,
    responseMessageId: response.message_id
  });
  await safeAppendConversation(
    store,
    buildConversationEntry({
      chatId,
      userId,
      messageId: response.message_id,
      direction: "out",
      text,
      payloadType: "text"
    }),
    "message.outbound_log_failed"
  );
  return response;
}

async function sendVideoLogged(
  bot: TelegramBot,
  store: DataStore,
  chatId: string,
  userId: string,
  filePath: string,
  caption: string
): Promise<void> {
  logInfo("telegram.send_video.start", {
    chatId,
    userId,
    filePath,
    captionLength: caption.length
  });
  const response = await bot.sendVideo(chatId, filePath, { caption });
  logInfo("telegram.send_video.done", {
    chatId,
    userId,
    responseMessageId: response.message_id
  });
  await safeAppendConversation(
    store,
    buildConversationEntry({
      chatId,
      userId,
      messageId: response.message_id,
      direction: "out",
      text: caption,
      payloadType: "video"
    }),
    "video.outbound_log_failed"
  );
}

interface SendVideoWithRetryParams {
  bot: TelegramBot;
  store: DataStore;
  queueItemId: string;
  chatId: string;
  userId: string;
  filePath: string;
  caption: string;
}

async function sendVideoWithRetry(params: SendVideoWithRetryParams): Promise<void> {
  const { bot, store, queueItemId, chatId, userId, filePath, caption } = params;
  let attempt = 0;

  while (true) {
    attempt += 1;
    if (attempt > 1) {
      logInfo("queue_item.send_video.retrying", {
        queueItemId,
        retryAttempt: attempt - 1,
        maxRetries: TELEGRAM_SEND_VIDEO_RETRY_DELAYS_MS.length
      });
    }

    try {
      await sendVideoLogged(bot, store, chatId, userId, filePath, caption);
      return;
    } catch (error: any) {
      const retryable = isRetryableTelegramUploadError(error);
      const retryIndex = attempt - 1;
      const delayMs = TELEGRAM_SEND_VIDEO_RETRY_DELAYS_MS[retryIndex];

      logWarn("queue_item.send_video.attempt_failed", {
        queueItemId,
        attempt,
        retryable,
        error: error?.message ?? String(error)
      });

      if (!retryable || typeof delayMs !== "number") {
        if (retryable) {
          const tagged = tagRetryableTelegramUploadFailure(error);
          logError("queue_item.send_video.give_up", {
            queueItemId,
            attemptsTried: attempt,
            maxRetries: TELEGRAM_SEND_VIDEO_RETRY_DELAYS_MS.length,
            error: tagged.message
          });
          throw tagged;
        }
        throw error;
      }

      logWarn("queue_item.send_video.retry_scheduled", {
        queueItemId,
        retryAttempt: retryIndex + 1,
        maxRetries: TELEGRAM_SEND_VIDEO_RETRY_DELAYS_MS.length,
        delayMs,
        error: error?.message ?? String(error)
      });
      await sleep(delayMs);
    }
  }
}

function isRetryableTelegramUploadError(error: unknown): boolean {
  const message = ((error as any)?.message ?? String(error)).toLowerCase();
  return (
    message.includes("socket hang up") ||
    message.includes("etimedout") ||
    message.includes("econnreset") ||
    message.includes("connect timeout")
  );
}

function tagRetryableTelegramUploadFailure(error: unknown): Error {
  const normalized = error instanceof Error ? error : new Error(String(error));
  (normalized as any).isRetryableTelegramUploadFailure = true;
  return normalized;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

async function safeUnlink(filePath: string | null): Promise<void> {
  if (!filePath) {
    return;
  }
  try {
    logInfo("file.cleanup.delete.start", { filePath });
    await fs.unlink(filePath);
    logInfo("file.cleanup.delete.done", { filePath });
  } catch (error: any) {
    if (error?.code !== "ENOENT") {
      logWarn("file.cleanup.delete_failed", {
        filePath,
        error: error?.message ?? error
      });
      console.warn(`Unable to delete file ${filePath}:`, error?.message ?? error);
    }
  }
}

async function safeUpsertUserSettings(store: DataStore, chatId: string): Promise<void> {
  try {
    await store.upsertUserSettings(chatId);
    logInfo("store.user_settings_upserted", { chatId });
  } catch (error: any) {
    logWarn("store.user_settings_upsert_failed", {
      chatId,
      error: error?.message ?? String(error)
    });
  }
}

async function safeAppendConversation(
  store: DataStore,
  entry: ConversationEntry,
  eventName: string
): Promise<void> {
  try {
    await store.appendConversation(entry);
  } catch (error: any) {
    logWarn(eventName, {
      chatId: entry.chatId,
      userId: entry.userId,
      direction: entry.direction,
      payloadType: entry.payloadType,
      error: error?.message ?? String(error)
    });
  }
}

interface ProgressMessageRegistration {
  queueItemId: string;
  chatId: string;
  messageId: number;
  url: string;
  initialStatus: string;
}

interface ProgressMessageSession {
  queueItemId: string;
  chatId: string;
  messageId: number;
  url: string;
  lastStatus: string;
  history: string[];
  editChain: Promise<void>;
  closed: boolean;
}

class ProgressMessageReporter {
  private readonly sessions = new Map<string, ProgressMessageSession>();

  constructor(private readonly bot: TelegramBot) {}

  register(registration: ProgressMessageRegistration): void {
    this.sessions.set(registration.queueItemId, {
      queueItemId: registration.queueItemId,
      chatId: registration.chatId,
      messageId: registration.messageId,
      url: registration.url,
      lastStatus: registration.initialStatus,
      history: [this.withTime(registration.initialStatus)],
      editChain: Promise.resolve(),
      closed: false
    });
  }

  handleLog(level: "INFO" | "WARN" | "ERROR", event: string, data?: Record<string, unknown>): void {
    const queueItemId = typeof data?.queueItemId === "string" ? data.queueItemId : null;
    if (!queueItemId) {
      return;
    }
    const session = this.sessions.get(queueItemId);
    if (!session || session.closed) {
      return;
    }

    const progress = buildProgressStatusFromLog(level, event, data);
    if (!progress) {
      return;
    }

    this.enqueueUpdate(session, progress.status, progress.terminal);
  }

  private enqueueUpdate(session: ProgressMessageSession, status: string, terminal: boolean): void {
    if (session.closed) {
      return;
    }

    session.editChain = session.editChain
      .then(async () => {
        if (session.closed) {
          return;
        }
        if (session.lastStatus === status) {
          if (terminal) {
            session.closed = true;
            this.sessions.delete(session.queueItemId);
          }
          return;
        }

        session.lastStatus = status;
        session.history.push(this.withTime(status));
        if (session.history.length > 8) {
          session.history = session.history.slice(-8);
        }
        const text = buildProgressMessageText(session);

        try {
          await this.bot.editMessageText(text, {
            chat_id: session.chatId,
            message_id: session.messageId
          });
        } catch (error: any) {
          const message = error?.message ?? String(error);
          if (!isIgnorableEditMessageError(message)) {
            console.warn(
              "[bot]",
              JSON.stringify({
                ts: new Date().toISOString(),
                level: "WARN",
                event: "progress_message.edit_failed",
                queueItemId: session.queueItemId,
                chatId: session.chatId,
                messageId: session.messageId,
                error: message
              })
            );
          }
        } finally {
          if (terminal) {
            session.closed = true;
            this.sessions.delete(session.queueItemId);
          }
        }
      })
      .catch((error) => {
        console.warn(
          "[bot]",
          JSON.stringify({
            ts: new Date().toISOString(),
            level: "WARN",
            event: "progress_message.update_chain_failed",
            queueItemId: session.queueItemId,
            error: (error as any)?.message ?? String(error)
          })
        );
      });
  }

  private withTime(status: string): string {
    const time = new Date().toLocaleTimeString("zh-TW", { hour12: false });
    return `${time} ${status}`;
  }
}

function buildProgressMessageText(session: ProgressMessageSession): string {
  const urlLine = truncateMiddle(session.url, 120);
  return [
    "下載進度更新",
    `目前狀態：${session.lastStatus}`,
    `網址：${urlLine}`,
    "",
    "最近進度：",
    ...session.history.map((line) => `- ${line}`)
  ].join("\n");
}

function buildProgressStatusFromLog(
  level: "INFO" | "WARN" | "ERROR",
  event: string,
  data?: Record<string, unknown>
): { status: string; terminal: boolean } | null {
  switch (event) {
    case "queue.enqueue_request":
      return { status: "正在加入佇列...", terminal: false };
    case "queue.enqueued": {
      const position = typeof data?.position === "number" ? data.position : null;
      return {
        status: position ? `已加入佇列，目前排隊第 ${position} 位。` : "已加入佇列，準備開始處理。",
        terminal: false
      };
    }
    case "queue_item.start":
      return { status: "開始處理下載任務。", terminal: false };
    case "queue_item.duration_check.start":
      return { status: "正在取得影片資訊（長度檢查）...", terminal: false };
    case "queue_item.duration_check.done": {
      const durationSeconds = typeof data?.durationSeconds === "number" ? data.durationSeconds : null;
      return durationSeconds === null
        ? { status: "影片資訊取得完成，稍後會用 ffprobe 再檢查長度。", terminal: false }
        : { status: `影片長度檢查完成（${formatDuration(durationSeconds)}）。`, terminal: false };
    }
    case "queue_item.download.start":
      return { status: "開始下載影片...", terminal: false };
    case "queue_item.download.done":
      return { status: "影片下載完成，正在檢查檔案資訊。", terminal: false };
    case "queue_item.file_stat": {
      const bytes = typeof data?.bytes === "number" ? data.bytes : null;
      return bytes === null
        ? { status: "已取得檔案資訊。", terminal: false }
        : { status: `已取得檔案資訊（大小 ${formatFileSize(bytes)}）。`, terminal: false };
    }
    case "queue_item.ffprobe_duration.start":
      return { status: "正在用 ffprobe 補查影片長度...", terminal: false };
    case "queue_item.ffprobe_duration.done": {
      const durationSeconds = typeof data?.durationSeconds === "number" ? data.durationSeconds : null;
      return durationSeconds === null
        ? { status: "ffprobe 無法取得影片長度。", terminal: false }
        : { status: `ffprobe 長度檢查完成（${formatDuration(durationSeconds)}）。`, terminal: false };
    }
    case "queue_item.rejected_duration_pre_download":
    case "queue_item.rejected_duration_post_download": {
      const durationSeconds = typeof data?.durationSeconds === "number" ? data.durationSeconds : null;
      return {
        status:
          durationSeconds === null
            ? "影片長度超過限制，已取消下載。"
            : `影片長度 ${formatDuration(durationSeconds)} 超過限制，已取消下載。`,
        terminal: true
      };
    }
    case "queue_item.rejected_size": {
      const bytes = typeof data?.bytes === "number" ? data.bytes : null;
      return {
        status:
          bytes === null
            ? "檔案大小超過 Telegram 上限，已取消回傳。"
            : `檔案大小 ${formatFileSize(bytes)} 超過 Telegram 上限，已取消回傳。`,
        terminal: true
      };
    }
    case "queue_item.azure_upload.start": {
      const bytes = typeof data?.bytes === "number" ? data.bytes : null;
      return {
        status:
          bytes === null
            ? "檔案超過 Telegram 上限，改為上傳 Azure Blob..."
            : `檔案大小 ${formatFileSize(bytes)} 超過 Telegram 上限，改為上傳 Azure Blob...`,
        terminal: false
      };
    }
    case "queue_item.azure_upload.done":
      return { status: "已上傳到 Azure Blob，正在回覆下載連結...", terminal: false };
    case "queue_item.recorded_blob_upload":
      return { status: "已完成，下載連結已回覆。", terminal: true };
    case "queue_item.azure_upload.failed":
      return { status: "改上傳 Azure Blob 失敗，已回覆原因。", terminal: true };
    case "queue_item.duration_unknown":
      return { status: "無法判斷影片長度，已取消回傳。", terminal: true };
    case "queue_item.send_video.start":
      return { status: "正在上傳影片到 Telegram...", terminal: false };
    case "queue_item.send_video.retry_scheduled": {
      const retryAttempt = typeof data?.retryAttempt === "number" ? data.retryAttempt : null;
      const maxRetries = typeof data?.maxRetries === "number" ? data.maxRetries : null;
      const delayMs = typeof data?.delayMs === "number" ? data.delayMs : null;
      const delaySeconds = delayMs === null ? null : Math.round(delayMs / 1000);
      const attemptText =
        retryAttempt !== null && maxRetries !== null
          ? `（第 ${retryAttempt} / ${maxRetries} 次重試）`
          : "";
      const delayText = delaySeconds === null ? "" : `，${delaySeconds} 秒後重試`;
      return {
        status: `上傳 Telegram 失敗${attemptText}${delayText}。`,
        terminal: false
      };
    }
    case "queue_item.send_video.retrying": {
      const retryAttempt = typeof data?.retryAttempt === "number" ? data.retryAttempt : null;
      return {
        status:
          retryAttempt === null
            ? "正在重新上傳影片到 Telegram..."
            : `正在重新上傳影片到 Telegram（第 ${retryAttempt} 次重試）...`,
        terminal: false
      };
    }
    case "queue_item.send_video.done":
      return { status: "影片已上傳完成，正在整理紀錄...", terminal: false };
    case "queue_item.send_video.give_up":
      return { status: "上傳失敗（已完成重試），檔案已保留供後續重試。", terminal: true };
    case "queue_item.recorded_sent":
      return { status: "已完成，影片已傳送。", terminal: true };
    case "queue_item.failed": {
      const errorMessage = typeof data?.error === "string" ? data.error : "下載失敗";
      return { status: `處理失敗：${errorMessage}`, terminal: true };
    }
    default:
      return level === "ERROR" && event.startsWith("queue_item.")
        ? { status: `處理失敗：${event}`, terminal: true }
        : null;
  }
}

function isIgnorableEditMessageError(message: string): boolean {
  const normalized = message.toLowerCase();
  return (
    normalized.includes("message is not modified") ||
    normalized.includes("message to edit not found") ||
    normalized.includes("message can't be edited")
  );
}

function truncateMiddle(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }
  const head = Math.ceil((maxLength - 3) / 2);
  const tail = Math.floor((maxLength - 3) / 2);
  return `${value.slice(0, head)}...${value.slice(value.length - tail)}`;
}

function previewText(value: string, maxLength = 120): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }
  return `${normalized.slice(0, maxLength)}...`;
}

function logInfo(event: string, data?: Record<string, unknown>): void {
  logWithLevel("INFO", event, data);
}

function logWarn(event: string, data?: Record<string, unknown>): void {
  logWithLevel("WARN", event, data);
}

function logError(event: string, data?: Record<string, unknown>): void {
  logWithLevel("ERROR", event, data);
}

function logWithLevel(level: "INFO" | "WARN" | "ERROR", event: string, data?: Record<string, unknown>): void {
  const payload = {
    ts: new Date().toISOString(),
    level,
    event,
    ...data
  };
  if (level === "ERROR") {
    console.error("[bot]", JSON.stringify(payload));
    progressMessageReporter?.handleLog(level, event, data);
    return;
  }
  if (level === "WARN") {
    console.warn("[bot]", JSON.stringify(payload));
    progressMessageReporter?.handleLog(level, event, data);
    return;
  }
  console.info("[bot]", JSON.stringify(payload));
  progressMessageReporter?.handleLog(level, event, data);
}
