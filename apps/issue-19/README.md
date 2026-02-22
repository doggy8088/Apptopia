# Issue #19: [工具] 開源個人記帳理財工具（Open Moneybook）

## 簡介

Open Moneybook 是純前端、隱私優先的個人記帳理財工具，資料僅保存在本機的 IndexedDB。V1 支援收入/支出記錄、分類預算追蹤、月摘要與 CSV 匯入匯出。

## 安裝

```bash
cd apps/issue-19
npm install
```

## 使用

```bash
cd apps/issue-19
# 直接開啟 index.html 或使用任何靜態伺服器
npx serve .
```

## 測試

```bash
cd apps/issue-19
npm test
```

## 建置

```bash
cd apps/issue-19
npm run build
```

## 部署

- GitHub Pages：CI 會產生 `dist/` 供部署使用。

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/19
- CI/CD Workflow: `.github/workflows/ci_19.yml`
