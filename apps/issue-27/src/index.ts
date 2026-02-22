import path from "node:path";
import { runBot } from "./bot";

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) {
  console.error("Missing TELEGRAM_BOT_TOKEN environment variable.");
  process.exit(1);
}

const dataDir = process.env.DATA_DIR
  ? path.resolve(process.env.DATA_DIR)
  : path.resolve(process.cwd(), "data");
const ytDlpPath = process.env.YT_DLP_PATH ?? "yt-dlp";

runBot({ token, dataDir, ytDlpPath }).catch((error) => {
  console.error("Bot failed to start:", error);
  process.exit(1);
});
