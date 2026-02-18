# Issue #6: Markdown Link Health Checker / Markdown 連結健康檢查器

> **English**: A CLI tool to check the health of links in Markdown files, supporting GitHub repositories, local folders, HTTP/HTTPS links, relative paths, and anchor links. Features include parallel processing, smart typo suggestions, JSON output, and zero dependencies (uses only Python standard library).

> **中文**：一個用於檢查 Markdown 文件中連結健康狀態的 CLI 工具，支援 GitHub Repository、本地資料夾、HTTP/HTTPS 連結、相對路徑和錨點連結。功能包括並行處理、智慧拼寫建議、JSON 輸出，且零依賴（僅使用 Python 標準庫）。

---

## 簡介

`mdlinkcheck` 是一個 CLI 工具，用於檢查 Markdown 文件中連結的健康狀態。它可以驗證外部 URL、相對路徑和錨點連結，幫助維護者及早發現失效的連結。

## 功能特色

- ✅ 支援 GitHub Repository URL 和本地資料夾
- ✅ 檢查 HTTP/HTTPS 外部連結
  - 智慧處理伺服器限制（自動重試不同請求方法）
  - 識別 Cloudflare Challenge（標記為 warning 而非 broken）
- ✅ 驗證相對路徑檔案是否存在
- ✅ 檢查錨點連結是否對應標題
- ✅ 並行請求加速檢查
- ✅ 自動忽略程式碼區塊中的連結
- ✅ 錨點拼寫建議（"did you mean?"）
- ✅ 支援 JSON 格式輸出
- ✅ 支援 `.mdlinkcheckrc` 設定檔
- ✅ 零依賴（僅使用 Python 標準庫）

## 安裝

```bash
cd apps/issue-6
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## 使用方式

### 基本用法

```bash
# 檢查本地資料夾
mdlinkcheck /path/to/folder

# 檢查當前目錄
mdlinkcheck .

# 檢查 GitHub Repository
mdlinkcheck https://github.com/owner/repo
```

### 進階選項

```bash
# 輸出 JSON 格式
mdlinkcheck . --format json

# 使用自訂設定檔
mdlinkcheck . --config my-config.json

# 調整並行數與逾時時間
mdlinkcheck . --max-workers 20 --timeout 15
```

### 輸出範例

```
🔍 Scanning: doggy8088/Apptopia (5 markdown files found)

README.md
  ❌ [404] https://example.com/old-api-doc (line 32)
  ❌ [404] https://expired-domain.io/guide (line 58)
  ⚠️ [timeout] https://slow-server.org/status (line 71)
  ✅ 12 links OK

docs/SETUP.md
  ❌ [file not found] ./images/architecture.png (line 15)
  ❌ [anchor not found] #installatoin (line 8)
     did you mean #installation?
  ✅ 6 links OK

CONTRIBUTING.md
  ✅ 4 links OK — all good!

────────────────────────────
📊 Summary
  Files scanned:  5
  Links checked:  25
  ✅ Healthy:     22
  ❌ Broken:       4
  ⚠️ Warning:      1
```

## 設定檔

建立 `.mdlinkcheckrc` 檔案來排除特定 URL 模式：

```json
{
  "exclude_urls": [
    "^https?://localhost",
    "^https?://127\\.0\\.0\\.1",
    "^https?://.*\\.local"
  ]
}
```

## 退出碼

- `0`: 所有連結健康
- `1`: 發現失效或有問題的連結

這讓工具可以輕鬆整合到 CI/CD 流程中。

## CI/CD 整合

### GitHub Actions 範例

```yaml
name: Check Markdown Links

on:
  push:
    paths:
      - '**.md'
  pull_request:
    paths:
      - '**.md'

jobs:
  check-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install mdlinkcheck
        run: |
          pip install mdlinkcheck
      
      - name: Check links
        run: mdlinkcheck .
```

## 測試

```bash
cd apps/issue-6
pytest
```

## 建置

```bash
cd apps/issue-6
python -m build
```

## 部署

此專案屬於 CLI 工具，CI 會在 `main` 分支 push 且測試通過後，上傳 `dist/` 為 GitHub Actions Artifacts。

## 架構說明

專案採用模組化設計：

- `cli.py`: CLI 入口點與參數解析
- `scanner.py`: Markdown 檔案掃描與連結提取
- `checker.py`: 連結健康檢查核心邏輯
- `reporter.py`: 報表生成（文字/JSON）
- `config.py`: 設定檔管理

## 技術細節

### 連結分類

工具會自動分類三種連結類型：

1. **HTTP 連結**: `http://` 或 `https://` 開頭
2. **相對路徑**: 本地檔案路徑（如 `./docs/setup.md`）
3. **錨點連結**: `#` 開頭，對應文件內標題

### 程式碼區塊處理

工具會自動忽略以下位置的連結：

- 圍欄式程式碼區塊（\`\`\` 或 \~\~\~）
- 行內程式碼（\`code\`）
- 縮排程式碼區塊（4 空格或 1 個 Tab）

### 錨點生成規則

錨點驗證使用 GitHub 風格的規則：

1. 轉換為小寫
2. 空格替換為連字號
3. 移除非英數字元（保留連字號）
4. 移除連續連字號
5. 移除前後連字號

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/6
- CI/CD Workflow: `.github/workflows/ci_6.yml`

## License

MIT
