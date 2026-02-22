import http from "node:http";
import https from "node:https";
import path from "node:path";
import { createReadStream, promises as fs } from "node:fs";

const AZURE_BLOB_API_VERSION = "2023-11-03";
const UPLOAD_TIMEOUT_MS = 10 * 60 * 1000;

export interface AzureBlobUploadResult {
  blobName: string;
  blobUrl: string;
  accessUrl: string;
}

export class AzureBlobUploadConfigError extends Error {}

export class AzureBlobUploadHttpError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly responseBody: string
  ) {
    super(message);
    this.name = "AzureBlobUploadHttpError";
  }
}

export function buildAzureBlobBlobUrl(containerSasUrl: string, blobName: string): URL {
  let containerUrl: URL;
  try {
    containerUrl = new URL(containerSasUrl);
  } catch {
    throw new AzureBlobUploadConfigError("Azure Blob SAS URL 格式無效。");
  }

  if (containerUrl.protocol !== "https:" && containerUrl.protocol !== "http:") {
    throw new AzureBlobUploadConfigError("Azure Blob SAS URL 必須使用 HTTP 或 HTTPS。");
  }
  if (!containerUrl.search) {
    throw new AzureBlobUploadConfigError("Azure Blob SAS URL 缺少 SAS 參數，請提供完整的 Container SAS URL。");
  }
  if (!blobName.trim()) {
    throw new AzureBlobUploadConfigError("Azure Blob 檔名不能是空白。");
  }

  const encodedBlobName = blobName
    .split("/")
    .filter((segment) => segment.length > 0)
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  if (!encodedBlobName) {
    throw new AzureBlobUploadConfigError("Azure Blob 檔名格式無效。");
  }

  const uploadUrl = new URL(containerUrl.toString());
  uploadUrl.pathname = `${containerUrl.pathname.replace(/\/+$/, "")}/${encodedBlobName}`;
  return uploadUrl;
}

export function buildAzureBlobObjectName(filePath: string, prefix: string): string {
  const ext = normalizeExtension(path.extname(filePath));
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${prefix}/${timestamp}${ext}`;
}

export async function uploadFileToAzureBlobContainer(params: {
  containerSasUrl: string;
  filePath: string;
  blobName: string;
  contentType?: string;
}): Promise<AzureBlobUploadResult> {
  const { containerSasUrl, filePath, blobName } = params;
  const uploadUrl = buildAzureBlobBlobUrl(containerSasUrl, blobName);
  const stats = await fs.stat(filePath);
  const contentType = params.contentType ?? guessContentType(filePath);

  await putBlob({
    url: uploadUrl,
    filePath,
    contentLength: stats.size,
    contentType
  });

  const blobUrl = new URL(uploadUrl.toString());
  blobUrl.search = "";

  return {
    blobName,
    blobUrl: blobUrl.toString(),
    accessUrl: uploadUrl.toString()
  };
}

export function describeAzureBlobUploadFailure(error: unknown): string {
  if (error instanceof AzureBlobUploadConfigError) {
    return error.message;
  }

  if (error instanceof AzureBlobUploadHttpError) {
    const status = error.statusCode;
    const serviceMessage = extractAzureServiceMessage(error.responseBody);
    if (status === 403) {
      return "Azure Storage 拒絕上傳（SAS 可能已過期或權限不足，HTTP 403）。";
    }
    if (status === 404) {
      return "找不到指定的 Azure Blob Container（HTTP 404）。";
    }
    if (status === 409) {
      return "Azure Storage 暫時無法接受這次上傳（HTTP 409）。";
    }
    if (status === 413) {
      return "Azure Storage 拒絕這個檔案大小或請求內容（HTTP 413）。";
    }
    if (serviceMessage) {
      return `Azure Storage 上傳失敗（HTTP ${status}）：${serviceMessage}`;
    }
    return `Azure Storage 上傳失敗（HTTP ${status}）。`;
  }

  const code = typeof (error as any)?.code === "string" ? (error as any).code : "";
  if (code === "ENOTFOUND" || code === "EAI_AGAIN") {
    return "無法連線到 Azure Storage（DNS 解析失敗）。";
  }
  if (code === "ECONNREFUSED") {
    return "無法連線到 Azure Storage（連線被拒絕）。";
  }
  if (code === "ETIMEDOUT") {
    return "連線 Azure Storage 逾時，請稍後再試。";
  }
  if (code === "ECONNRESET") {
    return "上傳 Azure Storage 時連線中斷，請稍後再試。";
  }

  const message = (error as any)?.message;
  return typeof message === "string" && message.trim().length > 0
    ? `Azure Blob 上傳失敗：${message}`
    : "Azure Blob 上傳失敗，請檢查 SAS URL 與網路連線。";
}

async function putBlob(params: {
  url: URL;
  filePath: string;
  contentLength: number;
  contentType: string;
}): Promise<void> {
  const transport = params.url.protocol === "http:" ? http : https;

  await new Promise<void>((resolve, reject) => {
    let finished = false;
    const request = transport.request(
      params.url,
      {
        method: "PUT",
        headers: {
          "x-ms-blob-type": "BlockBlob",
          "x-ms-version": AZURE_BLOB_API_VERSION,
          "x-ms-date": new Date().toUTCString(),
          "content-type": params.contentType,
          "content-length": String(params.contentLength)
        }
      },
      (response) => {
        const chunks: Buffer[] = [];
        response.on("data", (chunk) => {
          chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk)));
        });
        response.on("end", () => {
          if (finished) {
            return;
          }
          finished = true;
          const body = Buffer.concat(chunks).toString("utf8");
          if (response.statusCode === 201) {
            resolve();
            return;
          }
          reject(
            new AzureBlobUploadHttpError(
              `Azure Blob upload failed with status ${response.statusCode ?? 0}.`,
              response.statusCode ?? 0,
              body
            )
          );
        });
      }
    );

    request.setTimeout(UPLOAD_TIMEOUT_MS, () => {
      request.destroy(Object.assign(new Error("Azure Blob upload request timed out."), { code: "ETIMEDOUT" }));
    });

    request.on("error", (error) => {
      if (finished) {
        return;
      }
      finished = true;
      reject(error);
    });

    const readStream = createReadStream(params.filePath);
    readStream.on("error", (error) => {
      request.destroy(error);
    });
    readStream.pipe(request);
  });
}

function normalizeExtension(ext: string): string {
  if (!ext) {
    return ".mp4";
  }
  const safe = ext.toLowerCase();
  return /^[a-z0-9.]{1,16}$/.test(safe) ? safe : ".bin";
}

function guessContentType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".mp4":
      return "video/mp4";
    case ".mov":
      return "video/quicktime";
    case ".webm":
      return "video/webm";
    case ".mkv":
      return "video/x-matroska";
    default:
      return "application/octet-stream";
  }
}

function extractAzureServiceMessage(body: string): string | null {
  if (!body) {
    return null;
  }
  const match = body.match(/<Message>([\s\S]*?)<\/Message>/i);
  if (!match) {
    return null;
  }
  return match[1].replace(/\s+/g, " ").trim();
}
