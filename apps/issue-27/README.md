# Issue #27: 可自動下載影片的 Telegram Bot 機器人

## 簡介

此專案提供一個 Telegram Bot，使用 `yt-dlp` 下載影片並回傳 mp4。支援 `yt-dlp` 可處理的站點，並限制影片長度 60 分鐘、檔案大小 50 MB，同時拒絕本機或內網網址。

## 安裝

```bash
cd apps/issue-27
npm install
```

請先安裝 `yt-dlp`，並確保可在命令列中執行。
若影片來源無法提供長度資訊，會嘗試使用 `ffprobe` 讀取檔案長度，未安裝時會回覆錯誤。

## 使用

設定環境變數並啟動：

```bash
export TELEGRAM_BOT_TOKEN=your_token
export DATA_DIR=$(pwd)/data
export YT_DLP_PATH=yt-dlp
export AZURE_BLOB_CONTAINER_SAS_URL='https://<account>.blob.core.windows.net/<container>?<sas>'
npm start
```

可選用 `DATA_DIR` 指定資料儲存位置。`data/` 會保存：對話記錄、下載記錄、佇列狀態與使用者設定。
可選用 `AZURE_BLOB_CONTAINER_SAS_URL` 指定 Azure Storage Blob Container 的 SAS URL（完整 URL，含查詢參數）。設定後，若下載檔案超過 Telegram Bot 單檔上限，Bot 會改將檔案上傳到該 Blob Container，並直接回覆下載連結。

## 限制

- 影片長度上限：60 分鐘
- 影片檔案大小上限：50 MB（依 Telegram Bot API 文件，未來可能調整）
- 若未設定 `AZURE_BLOB_CONTAINER_SAS_URL`，超過 50 MB 會直接回覆無法回傳
- 若已設定 `AZURE_BLOB_CONTAINER_SAS_URL`，超過 50 MB 會改上傳到 Azure Blob 並回覆連結；若上傳失敗，會直接回覆可讀懂的失敗原因
- URL 長度上限：1000 bytes
- 本機/內網網址會直接拒絕（防止 SSRF 風險）
- 下載完成或拒絕回傳後，會移除暫存檔案避免磁碟占用

## Azure Blob 備援上傳（超過 50MB 時）

- 環境變數：`AZURE_BLOB_CONTAINER_SAS_URL`
- 內容需為「Container 層級」SAS URL（不是 Account URL，也不是 Blob URL）
- 建議 SAS 至少具備建立/寫入權限（如 `c`、`w`），若容器非公開且要讓使用者直接開啟連結，還需讀取權限（`r`）
- 你目前已在 Azure Storage Blob 設定保存期限為 7 天，Bot 回覆的連結所對應檔案會在超過 7 天後由 Azure 自動刪除
- SAS URL 本身也可能有自己的到期時間；若 SAS 過期或權限不足，Bot 會回覆上傳失敗原因（例如 403）

## 環境需求

- Node.js 22+
- 已安裝 `yt-dlp`（需在 PATH 或設定 `YT_DLP_PATH`）
- 若遇到無法取得影片長度的站點，可安裝 `ffprobe`（ffmpeg）以支援下載後長度檢查

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

此專案為 CLI/後端服務，建置後可透過 GitHub Actions Artifacts 下載產物。

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/27
- CI/CD Workflow: `.github/workflows/ci_27.yml`
