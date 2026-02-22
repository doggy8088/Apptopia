export type QueueStatus = "queued" | "processing" | "done" | "error";

export interface QueueItem {
  id: string;
  chatId: string;
  userId: string;
  url: string;
  status: QueueStatus;
  createdAt: string;
  updatedAt: string;
  error?: string;
}

export interface ConversationEntry {
  id: string;
  chatId: string;
  userId: string;
  username?: string;
  messageId?: number;
  direction: "in" | "out";
  text?: string;
  timestamp: string;
  payloadType: "text" | "video" | "system";
}

export interface DownloadRecord {
  id: string;
  url: string;
  chatId: string;
  userId: string;
  status:
    | "started"
    | "rejected_duration"
    | "rejected_size"
    | "sent"
    | "uploaded_blob"
    | "error"
    | "error_send_retryable"
    | "error_blob_upload";
  durationSeconds?: number;
  filePath?: string;
  fileSizeBytes?: number;
  createdAt: string;
  completedAt?: string;
  error?: string;
}

export interface UserSettings {
  chatId: string;
  createdAt: string;
  updatedAt: string;
  preferredFormat: "mp4";
}
