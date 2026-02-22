import path from "node:path";
import { runBot } from "./bot";

// Enable node-telegram-bot-api's improved file sending behavior and silence
// the NTBA_FIX_350 deprecation warning (official library toggle).
if (!process.env.NTBA_FIX_350) {
  process.env.NTBA_FIX_350 = "1";
}

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) {
  console.error("Missing TELEGRAM_BOT_TOKEN environment variable.");
  process.exit(1);
}

const dataDir = process.env.DATA_DIR
  ? path.resolve(process.env.DATA_DIR)
  : path.resolve(process.cwd(), "data");
const ytDlpPath = process.env.YT_DLP_PATH ?? "yt-dlp";
const azureBlobContainerSasUrl = process.env.AZURE_BLOB_CONTAINER_SAS_URL?.trim() || undefined;

runBot({ token, dataDir, ytDlpPath, azureBlobContainerSasUrl }).catch((error) => {
  console.error("Bot failed to start:", error);
  process.exit(1);
});
