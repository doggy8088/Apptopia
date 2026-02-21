import { describe, it, expect } from 'vitest';
import { DownloadQueue } from '../src/queue';
import { QueueStateItem } from '../src/storage';

function createItem(id: string): QueueStateItem {
  const now = new Date().toISOString();
  return {
    id,
    chatId: 1,
    url: 'https://example.com',
    status: 'queued',
    createdAt: now,
    updatedAt: now
  };
}

describe('DownloadQueue', () => {
  it('processes items sequentially', async () => {
    const processed: string[] = [];

    const queue = new DownloadQueue(
      [],
      async (item) => {
        processed.push(item.id);
        await new Promise((resolve) => setTimeout(resolve, 5));
      },
      () => {}
    );

    queue.enqueue(createItem('first'));
    queue.enqueue(createItem('second'));

    await queue.whenIdle();

    expect(processed).toEqual(['first', 'second']);
  });
});
