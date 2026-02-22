import type { QueueItem, QueueStatus } from "../types";

export type QueueUpdateHandler = (items: QueueItem[]) => Promise<void>;
export type QueueWorker = (item: QueueItem) => Promise<void>;

export class JobQueue {
  private items: QueueItem[];
  private readonly onUpdate: QueueUpdateHandler;
  private readonly worker: QueueWorker;
  private processing = false;

  constructor(initialItems: QueueItem[], onUpdate: QueueUpdateHandler, worker: QueueWorker) {
    this.items = [...initialItems];
    this.onUpdate = onUpdate;
    this.worker = worker;
  }

  getItems(): QueueItem[] {
    return [...this.items];
  }

  getPosition(id: string): number | null {
    const pending = this.items.filter((item) => item.status === "queued");
    const index = pending.findIndex((item) => item.id === id);
    if (index === -1) {
      return null;
    }
    return index + 1;
  }

  async enqueue(item: QueueItem): Promise<void> {
    this.items.push(item);
    await this.persist();
    void this.processNext();
  }

  private async updateStatus(id: string, status: QueueStatus, error?: string): Promise<void> {
    const now = new Date().toISOString();
    this.items = this.items.map((item) =>
      item.id === id
        ? {
            ...item,
            status,
            updatedAt: now,
            error: error ?? item.error
          }
        : item
    );
    await this.persist();
  }

  private async persist(): Promise<void> {
    await this.onUpdate(this.items);
  }

  private async processNext(): Promise<void> {
    if (this.processing) {
      return;
    }
    const next = this.items.find((item) => item.status === "queued");
    if (!next) {
      return;
    }
    this.processing = true;
    await this.updateStatus(next.id, "processing");
    try {
      await this.worker(next);
      await this.updateStatus(next.id, "done");
    } catch (error: any) {
      const message = error?.message ?? "未知錯誤";
      await this.updateStatus(next.id, "error", message);
    } finally {
      this.processing = false;
      void this.processNext();
    }
  }
}
