# Issue #45: PixelNest（像素窩：AI 代理遊戲化空間筆記）

## 簡介

PixelNest 是一個主打 Local-first 與視覺化整理的 PWA 筆記空間。透過像素房間與 Pixel Agent，把便條紙從玄關整理到書桌、床鋪、書櫃、冰箱，並支援 Markdown 內容、AI 自動分類、與 ZIP 匯出備份。

## 安裝

```bash
cd apps/issue-45
npm install
```

## 使用

```bash
# 使用任意靜態伺服器，例如
npx serve
```

瀏覽器開啟後可點擊家具進入 Markdown 編輯器，設定 BYOK API Key 後啟用 Auto-Sort。

## 測試

```bash
cd apps/issue-45
npm test
```

## 建置

```bash
cd apps/issue-45
npm run build
```

輸出會產生在 `apps/issue-45/dist/`。

## 部署

本專案禁止 GitHub Pages，請在 CI 中使用 GitHub Actions Artifacts 上傳 `dist/` 內容。

## 相關連結

- 原始 Issue: #45
- CI/CD Workflow: `.github/workflows/ci_45.yml`
