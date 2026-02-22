import { describe, expect, it } from "vitest";
import {
  AzureBlobUploadConfigError,
  AzureBlobUploadHttpError,
  buildAzureBlobBlobUrl,
  buildAzureBlobObjectName,
  describeAzureBlobUploadFailure
} from "../src/azureBlob";

describe("azureBlob", () => {
  it("builds blob upload URL from container SAS URL", () => {
    const url = buildAzureBlobBlobUrl(
      "https://example.blob.core.windows.net/videos?sv=2025-01-01&sp=rcw",
      "telegram-bot/chat-1/job-1/file name.mp4"
    );

    expect(url.toString()).toBe(
      "https://example.blob.core.windows.net/videos/telegram-bot/chat-1/job-1/file%20name.mp4?sv=2025-01-01&sp=rcw"
    );
  });

  it("requires a full container SAS URL", () => {
    expect(() =>
      buildAzureBlobBlobUrl("https://example.blob.core.windows.net/videos", "a.mp4")
    ).toThrow(AzureBlobUploadConfigError);
  });

  it("builds a stable object name with prefix and extension", () => {
    const objectName = buildAzureBlobObjectName("C:\\temp\\video.mp4", "telegram-bot/chat/job");

    expect(objectName.startsWith("telegram-bot/chat/job/")).toBe(true);
    expect(objectName.endsWith(".mp4")).toBe(true);
  });

  it("maps Azure HTTP failures to human-readable messages", () => {
    const error = new AzureBlobUploadHttpError("forbidden", 403, "<Error><Message>Denied</Message></Error>");

    expect(describeAzureBlobUploadFailure(error)).toContain("SAS");
    expect(describeAzureBlobUploadFailure(error)).toContain("403");
  });
});
