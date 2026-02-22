import { describe, expect, it } from "vitest";
import { JobQueue } from "../src/queue/jobQueue";
import type { QueueItem } from "../src/types";

const buildItem = (id: string): QueueItem => ({
  id,
  chatId: "chat",
  userId: "user",
  url: "https://example.com",
  status: "queued",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
});

describe("JobQueue", () => {
  it("processes jobs sequentially", async () => {
    const processed: string[] = [];
    const snapshots: QueueItem[][] = [];
    const queue = new JobQueue(
      [],
      async (items) => {
        snapshots.push(items.map((item) => ({ ...item })));
      },
      async (item) => {
        processed.push(item.id);
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    );

    await queue.enqueue(buildItem("a"));
    await queue.enqueue(buildItem("b"));

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(processed).toEqual(["a", "b"]);
    expect(snapshots.at(-1)?.every((item) => item.status === "done")).toBe(true);
  });
});
