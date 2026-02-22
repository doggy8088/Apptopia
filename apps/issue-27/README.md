# Issue #27: 可自動下載影片的 Telegram Bot 機器人

## 簡介

此專案提供一個 Telegram Bot，使用 `yt-dlp` 下載影片並回傳 mp4。支援 `yt-dlp` 可處理的站點，並限制影片長度 60 分鐘、檔案大小 50 MB。

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

## 測試

```bash
npm test
```

## 建置

```bash
npm run build
```

## 部署

此專案為 CLI/後端服務，建置後可透過 GitHub Actions Artifacts 下載產物。

## 相關連結

- 原始 Issue: #27
- CI/CD Workflow: `.github/workflows/ci_27.yml`
