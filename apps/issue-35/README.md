# Issue #35: 跑步機速度 - 配速換算計算器

## 簡介

跑步機速度（km/h）與跑者配速（min/km）雙向換算工具，支援深綠色暗色主題與 PWA 離線快取，適合健身房低光環境使用。

## 安裝

```bash
cd apps/issue-35
npm install
```

## 使用

```bash
cd apps/issue-35
# 直接開啟 index.html 或使用簡易伺服器
python -m http.server 8080
```

在瀏覽器開啟 `http://localhost:8080` 即可使用。PWA 離線功能需透過 http(s) 伺服器才能生效。

## 測試

```bash
cd apps/issue-35
npm test
```

## 建置

```bash
cd apps/issue-35
npm run build
```

## 部署

此專案為純前端應用，CI 會在 `main` 分支更新時部署到 GitHub Pages。部署產物位於 `apps/issue-35/dist`。

## 相關連結

- 原始 Issue: #35
- CI/CD Workflow: `.github/workflows/ci_35.yml`
