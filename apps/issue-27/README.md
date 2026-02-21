# Issue #27: Telegram 影片下載 Bot

## 簡介

這是一個以 Node.js + TypeScript 撰寫的 Telegram Bot。使用者傳入影片網址後，Bot 會透過 `yt-dlp` 下載影片並回傳，並且具備：

- 單工序佇列（一次只處理一部影片）
- 影片長度限制（預設 60 分鐘）
- Telegram Bot 檔案大小限制檢查
- 對話紀錄、下載紀錄、佇列狀態與使用者設定的持久化

## 安裝

```bash
cd apps/issue-27
npm install
```

## 使用

1. 安裝 `yt-dlp`（必須）。
2. 設定環境變數 `TELEGRAM_BOT_TOKEN`。
3. 啟動 Bot。

```bash
export TELEGRAM_BOT_TOKEN="<your-token>"
npm run start
```

可選環境變數：

- `DATA_DIR`：預設為 `apps/issue-27/data`
- `DOWNLOAD_DIR`：預設為 `apps/issue-27/downloads`
- `MAX_DURATION_MINUTES`：預設為 `60`
- `TELEGRAM_MAX_FILE_SIZE_MB`：預設為 `50`
- `MAX_URL_BYTES`：預設為 `1000`

備註：若影片 metadata 無法提供長度，Bot 會嘗試使用 `ffprobe` 取得長度；若環境沒有 `ffprobe`，會回覆無法辨識長度的錯誤訊息。

## 測試

```bash
cd apps/issue-27
npm test
```

## 建置

```bash
cd apps/issue-27
npm run build
```

## 部署

此為需要 Telegram Bot token 與本機 `yt-dlp` 的服務型應用，建議透過 CI 上傳 build artifacts 供部署使用。

## 相關連結

- Issue: #27
- CI/CD Workflow: `.github/workflows/ci_27.yml`
