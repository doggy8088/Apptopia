import path from 'path';
import { promises as fs } from 'fs';
import { config } from './config';
import { ensureDir, fileExists, writeJsonFile } from './utils/files';

export interface ConversationLogEntry {
  timestamp: string;
  chatId: number;
  userId?: number;
  username?: string;
  text?: string;
}

export interface DownloadLogEntry {
  timestamp: string;
  chatId: number;
  userId?: number;
  url: string;
  status: 'success' | 'error';
  errorMessage?: string;
  title?: string;
  durationSeconds?: number;
  fileSizeBytes?: number;
}

export interface QueueStateItem {
  id: string;
  chatId: number;
  userId?: number;
  messageId?: number;
  url: string;
  status: 'queued' | 'processing' | 'done' | 'error';
  createdAt: string;
  updatedAt: string;
  errorMessage?: string;
}

export interface UserSettings {
  [userId: string]: {
    createdAt: string;
    lastSeenAt: string;
  };
}

const conversationLogPath = path.join(config.dataDir, 'conversations.log.jsonl');
const downloadLogPath = path.join(config.dataDir, 'downloads.log.jsonl');
const queueStatePath = path.join(config.dataDir, 'queue.json');
const userSettingsPath = path.join(config.dataDir, 'user-settings.json');

async function appendJsonLine(pathname: string, data: unknown): Promise<void> {
  await fs.appendFile(pathname, `${JSON.stringify(data)}\n`, 'utf8');
}

export async function ensureStorageReady(): Promise<void> {
  await ensureDir(config.dataDir);
  await ensureDir(config.downloadDir);
}

export async function appendConversationLog(entry: ConversationLogEntry): Promise<void> {
  await appendJsonLine(conversationLogPath, entry);
}

export async function appendDownloadLog(entry: DownloadLogEntry): Promise<void> {
  await appendJsonLine(downloadLogPath, entry);
}

export async function loadQueueState(): Promise<QueueStateItem[]> {
  if (!(await fileExists(queueStatePath))) {
    return [];
  }
  const raw = await fs.readFile(queueStatePath, 'utf8');
  return JSON.parse(raw) as QueueStateItem[];
}

export async function saveQueueState(items: QueueStateItem[]): Promise<void> {
  await writeJsonFile(queueStatePath, items);
}

export async function loadUserSettings(): Promise<UserSettings> {
  if (!(await fileExists(userSettingsPath))) {
    return {};
  }
  const raw = await fs.readFile(userSettingsPath, 'utf8');
  return JSON.parse(raw) as UserSettings;
}

export async function saveUserSettings(settings: UserSettings): Promise<void> {
  await writeJsonFile(userSettingsPath, settings);
}

export async function upsertUserSettings(userId: number): Promise<UserSettings> {
  const settings = await loadUserSettings();
  const now = new Date().toISOString();
  const key = String(userId);

  if (!settings[key]) {
    settings[key] = { createdAt: now, lastSeenAt: now };
  } else {
    settings[key].lastSeenAt = now;
  }

  await saveUserSettings(settings);
  return settings;
}
