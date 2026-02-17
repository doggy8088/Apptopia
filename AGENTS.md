# Agent 開發指南

本文件定義了 Apptopia 專案中 AI Agent 開發的標準規則與最佳實踐。

## 目錄

- [專案結構規範](#專案結構規範)
- [CI/CD 工作流程規範](#cicd-工作流程規範)
- [部署策略](#部署策略)
- [技能管理](#技能管理)
- [開發流程](#開發流程)

## 專案結構規範

### 應用程式目錄結構

每個 Issue 開發的應用程式都應該建立在獨立的目錄中：

```
apps/
└── [issue_id]/
    ├── README.md              # 專案說明文件
    ├── package.json           # (如適用) Node.js 專案配置
    ├── requirements.txt       # (如適用) Python 依賴
    ├── src/                   # 原始碼目錄
    ├── tests/                 # 測試檔案
    ├── dist/                  # 建置輸出目錄
    └── docs/                  # 額外文件
```

**規則：**

- `[issue_id]` 應該使用 Issue 的編號（例如：`issue-1`, `issue-42`）
- 每個應用程式必須有獨立的 `README.md` 說明如何安裝、執行和測試
- 保持各應用程式之間的獨立性，避免共享依賴造成的耦合

### 範例目錄結構

```
apps/
├── issue-1/
│   ├── README.md
│   ├── index.html
│   └── styles.css
├── issue-2/
│   ├── README.md
│   ├── package.json
│   ├── src/
│   │   └── index.js
│   └── tests/
│       └── index.test.js
└── issue-3/
    ├── README.md
    ├── requirements.txt
    └── main.py
```

## CI/CD 工作流程規範

### 工作流程檔案命名

每個應用程式都應該有自己的 CI/CD 工作流程，檔案位置和命名規則如下：

```
.github/
└── workflows/
    ├── ci_[id].yml           # 專案專屬的 CI/CD 工作流程
    └── ...
```

**規則：**

- `[id]` 應該與 Issue 編號對應（例如：`ci_1.yml`, `ci_42.yml`）
- 工作流程檔案應該只在相關目錄有變更時觸發

### 工作流程範本

#### 基本結構

```yaml
name: CI for Issue [id]

on:
  push:
    paths:
      - 'apps/issue-[id]/**'
      - '.github/workflows/ci_[id].yml'
  pull_request:
    paths:
      - 'apps/issue-[id]/**'
      - '.github/workflows/ci_[id].yml'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup environment
        # ... 根據專案類型設置環境
      
      - name: Install dependencies
        working-directory: apps/issue-[id]
        run: |
          # ... 安裝依賴指令
      
      - name: Run tests
        working-directory: apps/issue-[id]
        run: |
          # ... 執行測試指令
      
      - name: Build
        working-directory: apps/issue-[id]
        run: |
          # ... 建置指令
```

#### 路徑觸發規則

工作流程應該限定只在以下情況觸發：

1. 專案目錄內的檔案有變更：`apps/issue-[id]/**`
2. 工作流程本身被修改：`.github/workflows/ci_[id].yml`

這樣可以確保：
- 不同專案的 CI 不會互相干擾
- 只有相關變更才會觸發建置，節省 CI 資源
- 加快回饋週期

## 部署策略

### 前端網頁應用程式

**部署目標：GitHub Pages**

對於純前端的網頁應用程式（HTML、CSS、JavaScript），應該部署到 GitHub Pages。

#### 部署工作流程範例

```yaml
  deploy:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: read
      pages: write
      id-token: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build
        working-directory: apps/issue-[id]
        run: |
          # ... 建置指令
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: apps/issue-[id]/dist
      
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

**判斷標準：**
- 不需要後端 API 或資料庫
- 所有邏輯都在客戶端執行
- 只使用靜態檔案（HTML、CSS、JavaScript）

### 後端應用程式、CLI 工具、腳本

**部署目標：Build Artifacts**

對於包含後端的應用程式、CLI 工具或腳本，應該將建置產物上傳為 GitHub Actions Artifacts。

#### 部署工作流程範例

```yaml
  package:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build
        working-directory: apps/issue-[id]
        run: |
          # ... 建置指令
      
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: issue-[id]-build
          path: |
            apps/issue-[id]/dist/
            apps/issue-[id]/build/
          retention-days: 90
```

**判斷標準：**
- 需要後端 API 伺服器
- 需要資料庫連線
- CLI 工具或命令列腳本
- 需要在伺服器環境執行的應用程式

### 部署決策流程圖

```
開始
  ↓
是否為純前端應用？
  ├─ 是 → 部署到 GitHub Pages
  └─ 否 → 
      ↓
  是否包含後端/API？
      ├─ 是 → 上傳為 Build Artifacts
      └─ 否 →
          ↓
      是否為 CLI 工具/腳本？
          ├─ 是 → 上傳為 Build Artifacts
          └─ 否 → 根據實際情況決定
```

## 技能管理

### 使用 find-skills 尋找技能

在開發過程中，遇到特定需求時，應該先嘗試使用 `find-skills` 技能來尋找是否有現成的技能可以協助。

#### 何時使用 find-skills

- 開始新功能開發時
- 遇到特定技術挑戰時
- 需要特定領域知識時
- 想要採用最佳實踐時

#### 使用方式

```bash
# 搜尋相關技能
npx skills find [query]

# 例如：
npx skills find react testing
npx skills find deployment
npx skills find api documentation
```

### 自動安裝技能

當找到相關技能後，應該安裝到專案中：

```bash
# 安裝特定技能到專案
npx skills add <owner/repo@skill>

# 例如：
npx skills add vercel-labs/agent-skills@vercel-react-best-practices
```

### 管理 Agent Skills

#### 建立自訂技能

當在開發過程中累積了寶貴經驗，應該將其整理為技能，以便後續開發使用。

```bash
# 初始化新技能
npx skills init my-custom-skill
```

#### 自訂技能目錄結構

```
.agents/
└── skills/
    ├── find-skills/           # 已安裝的外部技能
    └── custom/                # 專案自訂技能
        ├── apptopia-frontend/
        │   └── SKILL.md
        ├── apptopia-backend/
        │   └── SKILL.md
        └── apptopia-testing/
            └── SKILL.md
```

#### 技能檔案格式

每個技能應該包含一個 `SKILL.md` 檔案，格式如下：

```markdown
---
name: skill-name
description: 簡短的技能描述
---

# 技能名稱

## 何時使用此技能

- 使用情境 1
- 使用情境 2

## 如何使用

詳細的使用說明...

## 範例

實際範例...
```

### 技能更新與維護

定期檢查和更新技能：

```bash
# 檢查技能更新
npx skills check

# 更新所有技能
npx skills update
```

## 開發流程

### 標準開發流程

1. **開始開發前**
   - 閱讀 Issue 需求
   - 使用 `npx skills find` 搜尋相關技能
   - 安裝找到的相關技能

2. **開發階段**
   - 在 `apps/issue-[id]/` 目錄下建立專案
   - 建立專案專屬的 CI/CD 工作流程 `.github/workflows/ci_[id].yml`
   - 撰寫程式碼和測試
   - 記錄開發過程中的經驗和最佳實踐

3. **測試階段**
   - 確保測試覆蓋率足夠
   - 在 CI 中執行測試
   - 修正發現的問題

4. **部署階段**
   - 根據應用程式類型選擇部署策略
   - 前端應用：部署到 GitHub Pages
   - 後端/CLI：上傳 Build Artifacts

5. **經驗累積**
   - 將開發過程中的經驗整理為技能
   - 更新或建立新的自訂技能
   - 提交到 `.agents/skills/custom/` 目錄

### 自動化最佳實踐

- **持續整合**：每次提交都應該觸發 CI
- **自動化測試**：所有測試都應該在 CI 中自動執行
- **自動化部署**：通過所有測試後自動部署
- **技能管理**：定期更新和維護技能庫

### 文件規範

每個應用程式的 README.md 應該包含：

1. **專案簡介**：簡短描述應用程式的功能
2. **安裝步驟**：如何安裝依賴
3. **使用方式**：如何執行應用程式
4. **測試方式**：如何執行測試
5. **建置方式**：如何建置應用程式
6. **部署資訊**：如何存取已部署的應用程式
7. **相關 Issue**：連結到原始 Issue

### 範例 README.md

```markdown
# Issue #[id]: [標題]

## 簡介

[簡短描述這個應用程式的功能]

## 安裝

```bash
cd apps/issue-[id]
npm install  # 或其他套件管理器
```

## 使用

```bash
npm start    # 或其他執行指令
```

## 測試

```bash
npm test
```

## 建置

```bash
npm run build
```

## 部署

[部署資訊，例如 GitHub Pages URL 或如何下載 Artifacts]

## 相關連結

- 原始 Issue: #[id]
- CI/CD Workflow: [連結到工作流程]
```

## 常見問題

### Q: 如果一個 Issue 包含多個應用程式怎麼辦？

A: 應該拆分為多個 Issue，每個 Issue 對應一個應用程式。

### Q: 可以在不同應用程式之間共享程式碼嗎？

A: 盡量避免。如果確實需要共享，考慮建立獨立的函式庫專案。

### Q: 測試失敗時 CI 會如何處理？

A: CI 會失敗並阻止合併到主分支，必須修正測試後才能繼續。

### Q: 如何決定使用哪種部署策略？

A: 參考「部署策略」章節的決策流程圖。

### Q: 自訂技能應該包含什麼內容？

A: 包含開發過程中總結的最佳實踐、常用模式、注意事項等。

## 總結

遵循本文件的規範，可以確保：

- **一致性**：所有專案遵循相同的結構和命名規範
- **可維護性**：清晰的結構和文件讓維護更容易
- **自動化**：完整的 CI/CD 流程減少手動操作
- **知識累積**：技能系統幫助團隊累積和重用經驗
- **效率提升**：標準化流程加快開發速度

開發時請始終參考本文件，並在發現可以改進的地方時更新此文件。
