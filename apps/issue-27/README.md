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
npm start
```

可選用 `DATA_DIR` 指定資料儲存位置。`data/` 會保存：對話記錄、下載記錄、佇列狀態與使用者設定。

## 限制

- 影片長度上限：60 分鐘
- 影片檔案大小上限：50 MB（依 Telegram Bot API 文件，未來可能調整）
- URL 長度上限：1000 bytes
- 本機/內網網址會直接拒絕（防止 SSRF 風險）
- 下載完成或拒絕回傳後，會移除暫存檔案避免磁碟占用

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
