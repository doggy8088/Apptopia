import path from "node:path";
import { promises as fs } from "node:fs";
import type { ConversationEntry, DownloadRecord, QueueItem, UserSettings } from "../types";
import { ensureDir, readJsonFile, writeJsonFile } from "../utils/json";

export class DataStore {
  readonly baseDir: string;
  readonly downloadsDir: string;
  private readonly conversationsPath: string;
  private readonly downloadsPath: string;
  private readonly queuePath: string;
  private readonly settingsPath: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    this.downloadsDir = path.join(baseDir, "downloads");
    this.conversationsPath = path.join(baseDir, "conversations.json");
    this.downloadsPath = path.join(baseDir, "downloads.json");
    this.queuePath = path.join(baseDir, "queue.json");
    this.settingsPath = path.join(baseDir, "settings.json");
  }

  async ensure(): Promise<void> {
    await ensureDir(this.baseDir);
    await ensureDir(this.downloadsDir);
  }

  async appendConversation(entry: ConversationEntry): Promise<void> {
    const list = await readJsonFile<ConversationEntry[]>(this.conversationsPath, []);
    list.push(entry);
    await writeJsonFile(this.conversationsPath, list);
  }

  async appendDownload(entry: DownloadRecord): Promise<void> {
    const list = await readJsonFile<DownloadRecord[]>(this.downloadsPath, []);
    list.push(entry);
    await writeJsonFile(this.downloadsPath, list);
  }

  async loadQueue(): Promise<QueueItem[]> {
    return readJsonFile<QueueItem[]>(this.queuePath, []);
  }

  async saveQueue(items: QueueItem[]): Promise<void> {
    await writeJsonFile(this.queuePath, items);
  }

  async upsertUserSettings(chatId: string): Promise<UserSettings> {
    const settings = await readJsonFile<Record<string, UserSettings>>(this.settingsPath, {});
    const existing = settings[chatId];
    const now = new Date().toISOString();
    if (existing) {
      const updated = { ...existing, updatedAt: now };
      settings[chatId] = updated;
      await writeJsonFile(this.settingsPath, settings);
      return updated;
    }
    const created: UserSettings = {
      chatId,
      createdAt: now,
      updatedAt: now,
      preferredFormat: "mp4"
    };
    settings[chatId] = created;
    await writeJsonFile(this.settingsPath, settings);
    return created;
  }

  async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }
}
