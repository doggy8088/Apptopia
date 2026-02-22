# Issue #18: Obsidian Book Compiler

## 簡介

`obsidian-book` 是一個可離線執行的 CLI，用來掃描 Obsidian Vault，依 `--topic` 篩選筆記、建議章節順序，並輸出標準 Markdown 書稿 (`book.md`) 與 `book.yaml`。

## 安裝

```bash
cd apps/issue-18
npm install
```

## 使用

```bash
npm start -- --vault ~/MyVault --topic "#kubernetes" --output-dir ./output
```

使用指定設定檔並預覽章節結構：

```bash
npm start -- --vault ~/MyVault --topic "folder:DevOps/K8s" --config ./book.yaml --dry-run
```

常用參數：
- `--vault <path>`：Obsidian Vault 路徑
- `--topic <topic>`：主題篩選（`#tag`、`tag:xxx`、`folder:xxx`、`keyword:xxx`）
- `--config <path>`：自訂 `book.yaml`
- `--output-dir <path>`：輸出目錄（預設 `output`）
- `--output-format <format>`：僅支援 `markdown`
- `--dry-run`：僅輸出章節順序預覽，不寫檔

## 測試

```bash
npm test
```

## 建置

```bash
npm run build
```

## 部署

本專案為 CLI 工具，CI 會在 `main` 分支打包並上傳 build artifacts。請參考 `.github/workflows/ci_18.yml`。

## 相關連結

- 原始 Issue: #18
- CI/CD Workflow: `.github/workflows/ci_18.yml`
