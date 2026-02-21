# 開發者快速入門指南

歡迎加入 AI知識++ 專案！本文件將幫助你快速了解專案並開始貢獻。

---

## 專案概覽

**AI知識++** 是一個本機運作的私人知識庫桌面應用程式，支援：
- 📚 多格式知識管理（Markdown、圖片）
- 🤖 AI 驅動的問答系統（RAG）
- 🔗 智慧關聯分析與知識圖譜
- 💾 完全本機化，保護隱私

**目前狀態**：Phase 0 - 規劃階段（約 40% 完成）

---

## 5 分鐘快速了解

### 1. 閱讀順序（必讀）

如果你是第一次接觸本專案，建議按以下順序閱讀：

1. **README.md** (10 分鐘)
   - 了解專案目標與功能
   - 理解 V1 開發計畫
   - 查看驗收基準

2. **docs/ROADMAP.md** (15 分鐘)
   - 查看完整開發時程
   - 了解各 Phase 的目標
   - 確認交付物與完成標準

3. **docs/PHASE_0_STATUS.md** (5 分鐘)
   - 了解目前進度
   - 查看待完成任務
   - 知道下一步行動

4. **docs/TECHNICAL_ARCHITECTURE.md** (20 分鐘)
   - 理解技術架構
   - 查看技術選型理由
   - 了解核心演算法

### 2. 專案結構

```
apps/issue-3/
├── README.md                    # 專案主要說明
├── .gitignore                   # Git 忽略規則
├── src/                         # 原始碼（尚未開發）
├── tests/                       # 測試檔案（尚未開發）
├── data/
│   └── test-data/              # 測試資料集（43 MD + 74 圖片）
└── docs/
    ├── PHASE_0_PLANNING.md     # Phase 0 詳細規劃
    ├── PHASE_0_STATUS.md       # Phase 0 狀態追蹤
    ├── ROADMAP.md              # 開發路線圖（18 週）
    ├── TECHNICAL_ARCHITECTURE.md # 技術架構文件
    └── TEST_DATA_GUIDE.md      # 測試資料說明
```

### 3. 關鍵數字

- **開發時程**：3-4 個月（18 週）
- **開發階段**：5 個 Phase
- **測試資料**：43 個 Markdown 文件，74 張圖片
- **驗收題庫**：15+ 題（待完成）
- **目標平台**：Windows 10/11

---

## 開始貢獻

### Phase 0 待辦任務（當前）

以下是 Phase 0 還需要完成的任務，歡迎認領：

#### 🔥 高優先級

1. **Obsidian 語法支援清單**
   - **任務**：分析測試資料並定義語法支援策略
   - **預計時間**：2-3 天
   - **技能需求**：熟悉 Markdown 與 Obsidian
   - **交付物**：`docs/OBSIDIAN_SYNTAX_SUPPORT.md`

2. **驗收題庫建立**
   - **任務**：建立 15+ 個詳細測試案例
   - **預計時間**：3-5 天
   - **技能需求**：了解 RAG 問答系統、測試設計
   - **交付物**：`docs/ACCEPTANCE_TEST_CASES.md`

#### ⭐ 中優先級

3. **技術驗證**
   - **任務**：建立最小可行原型，驗證技術棧
   - **預計時間**：5-7 天
   - **技能需求**：Tauri、Python、Rust、向量資料庫
   - **交付物**：技術驗證報告與原型程式碼

---

## 開發環境設置

### 必要工具

```bash
# Node.js 18+ (用於 Tauri 前端)
node --version

# Python 3.10+ (用於 RAG 後端)
python --version

# Rust 1.70+ (用於效能關鍵模組與 Tauri)
rustc --version

# Git
git --version
```

### 可選工具

```bash
# Ollama (用於本機 LLM)
ollama --version

# PaddleOCR (用於圖片文字識別)
pip install paddleocr
```

### 克隆專案

```bash
# 克隆 repository
git clone https://github.com/doggy8088/Apptopia.git

# 進入專案目錄
cd Apptopia/apps/issue-3

# 查看目前狀態
cat docs/PHASE_0_STATUS.md
```

---

## 技術棧概覽

### 前端（桌面 UI）
- **框架**：Tauri (輕量級桌面應用框架)
- **UI 技術**：Svelte 或 React（待決定）
- **圖譜視覺化**：D3.js 或 Cytoscape.js

### 後端（核心邏輯）
- **主要語言**：Python（RAG、LLM 整合、資料處理）
- **效能模組**：Rust（向量檢索、檔案索引）
- **向量資料庫**：Chroma（嵌入式）
- **LLM**：Ollama（本機）或 OpenAI API（可選）
- **OCR**：PaddleOCR

---

## 開發流程

### 1. 選擇任務

查看 `docs/PHASE_0_STATUS.md` 中的待辦任務，選擇一個你感興趣且能力匹配的任務。

### 2. 建立分支

```bash
# 建立新分支
git checkout -b feature/your-task-name

# 例如：
git checkout -b feature/obsidian-syntax-support
```

### 3. 開發與測試

- 遵循專案的程式碼規範
- 撰寫清晰的註解
- 包含必要的測試

### 4. 提交 Pull Request

```bash
# 提交變更
git add .
git commit -m "feat: 簡短描述你的變更"

# 推送到 GitHub
git push origin feature/your-task-name
```

然後在 GitHub 上建立 Pull Request。

---

## 程式碼規範

### Commit Message 格式

```
<type>: <description>

[optional body]

[optional footer]
```

**Type 類型**：
- `feat`: 新功能
- `fix`: 修復 Bug
- `docs`: 文件變更
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置流程或輔助工具

**範例**：
```
feat: add Obsidian syntax support matrix

- Define fully supported syntax
- Define degraded syntax
- Document unsupported syntax
```

---

## 溝通管道

### Issue 討論

- 專案主要討論在 [Issue #3](https://github.com/doggy8088/Apptopia/issues/3)
- 有問題請在 Issue 中留言
- Tag 相關人員以獲得回應

### Pull Request Review

- 提交 PR 後會有團隊成員 review
- 根據回饋進行修正
- 獲得 approval 後會被 merge

---

## 學習資源

### RAG（檢索增強生成）
- [LangChain Documentation](https://python.langchain.com/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)

### Tauri
- [Tauri Official Guide](https://tauri.app/v1/guides/)
- [Tauri Examples](https://github.com/tauri-apps/tauri/tree/dev/examples)

### Chroma 向量資料庫
- [Chroma Documentation](https://docs.trychroma.com/)

### Obsidian
- [Obsidian Help](https://help.obsidian.md/)
- [Obsidian Developer Docs](https://docs.obsidian.md/)

---

## 常見問題

### Q: 我沒有 Tauri 經驗，可以參與嗎？
A: 可以！Phase 0 的任務不需要實際撰寫程式碼，主要是規劃與文件撰寫。

### Q: 我該從哪裡開始？
A: 建議先認領「Obsidian 語法支援清單」或「驗收題庫建立」任務，這些任務可以幫助你深入了解專案需求。

### Q: 開發需要使用 Windows 嗎？
A: Phase 0 不需要。後續開發階段建議有 Windows 環境進行測試，但開發可在任何平台進行。

### Q: 需要有 AI/ML 背景嗎？
A: 不一定。不同任務需要不同技能，Phase 0 的文件任務主要需要邏輯思維與文件撰寫能力。

### Q: 測試資料可以修改嗎？
A: 測試資料是從真實 Obsidian vault 取得，建議不要修改。如需額外測試資料，請建立新的資料集。

---

## 下一步

1. **立即行動**
   - [ ] 閱讀 README.md 與 ROADMAP.md
   - [ ] 瀏覽測試資料（`data/test-data/`）
   - [ ] 選擇一個 Phase 0 任務

2. **本週目標**
   - [ ] 熟悉專案結構與文件
   - [ ] 開始貢獻第一個任務
   - [ ] 在 Issue 中提問或討論

3. **長期參與**
   - [ ] 持續關注專案進度
   - [ ] 參與 Phase 1-5 的開發
   - [ ] 分享使用經驗與改進建議

---

## 致謝

感謝你對 AI知識++ 專案的興趣！我們期待你的貢獻。

如有任何問題，歡迎在 [Issue #3](https://github.com/doggy8088/Apptopia/issues/3) 中提問。

---

**最後更新**：2026-02-17  
**維護者**：[@doggy8088](https://github.com/doggy8088)  
**專案狀態**：Phase 0 進行中
