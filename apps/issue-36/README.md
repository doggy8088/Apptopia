# Issue #36: LinguistFlow

## 簡介

LinguistFlow 是一個 Chrome MV3 擴充功能，會在 YouTube 影片上方注入可選取的字幕層，讓使用者直接選取單字並一鍵寫入 Notion 資料庫，同時保留語境與簡單的詞性判斷。

## 安裝

```bash
cd apps/issue-36
npm install
```

## 使用

1. 建置擴充功能：

```bash
npm run build
```

2. 在 Chrome 開啟 `chrome://extensions`，開啟「開發人員模式」。
3. 點擊「載入未封裝項目」，選擇 `apps/issue-36/dist`。
4. 前往 YouTube 影片，開啟字幕。
5. 用滑鼠選取字幕層文字後右鍵，選擇「LinguistFlow: Add to Notion」。
6. 首次使用請在擴充功能選單點擊「擴充功能選項」並填寫 Notion API Key 與 Database ID。

## 測試

```bash
npm test
```

## 建置

```bash
npm run build
```

## 部署

此專案為瀏覽器擴充功能，CI 會產出 `apps/issue-36/dist` 並以 GitHub Actions Artifacts 形式提供下載。

## 相關連結

- 原始 Issue: #36
- CI/CD Workflow: `.github/workflows/ci_36.yml`
