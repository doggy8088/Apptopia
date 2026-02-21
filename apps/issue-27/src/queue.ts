import { QueueStateItem } from './storage';

export type QueueProcessor = (item: QueueStateItem) => Promise<void>;

export class DownloadQueue {
  private items: QueueStateItem[];
  private processing = false;
  private idleResolvers: Array<() => void> = [];

  constructor(
    items: QueueStateItem[],
    private readonly processor: QueueProcessor,
    private readonly onStateChange: (items: QueueStateItem[]) => Promise<void> | void
  ) {
    this.items = items;
  }

  enqueue(item: QueueStateItem): number {
    this.items.push(item);
    void this.onStateChange(this.items);
    const position = this.items.filter((entry) => entry.status === 'queued').length;
    void this.processNext();
    return position;
  }

  getSnapshot(): QueueStateItem[] {
    return [...this.items];
  }

  async whenIdle(): Promise<void> {
    if (!this.processing && !this.hasQueued()) {
      return;
    }

    return new Promise((resolve) => {
      this.idleResolvers.push(resolve);
    });
  }

  private hasQueued(): boolean {
    return this.items.some((entry) => entry.status === 'queued');
  }

  private resolveIdleIfNeeded(): void {
    if (this.processing || this.hasQueued()) {
      return;
    }
    while (this.idleResolvers.length > 0) {
      const resolve = this.idleResolvers.shift();
      resolve?.();
    }
  }

  private async processNext(): Promise<void> {
    if (this.processing) {
      return;
    }

    const nextItem = this.items.find((entry) => entry.status === 'queued');
    if (!nextItem) {
      this.resolveIdleIfNeeded();
      return;
    }

    this.processing = true;
    nextItem.status = 'processing';
    nextItem.updatedAt = new Date().toISOString();
    await this.onStateChange(this.items);

    try {
      await this.processor(nextItem);
      nextItem.status = 'done';
      nextItem.updatedAt = new Date().toISOString();
    } catch (error) {
      const err = error as Error;
      nextItem.status = 'error';
      nextItem.errorMessage = err.message;
      nextItem.updatedAt = new Date().toISOString();
    } finally {
      await this.onStateChange(this.items);
      this.processing = false;
      this.resolveIdleIfNeeded();
      void this.processNext();
    }
  }
}
