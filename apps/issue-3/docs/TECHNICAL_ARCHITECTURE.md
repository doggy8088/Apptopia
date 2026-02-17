# 技術架構規劃

## 概述

本文件定義 AI知識++ V1 的技術架構，包括技術選型、系統架構、資料流程和實作細節。

---

## 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 UI Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  對話介面    │  │  知識圖譜    │  │  設定管理    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    應用邏輯 Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  RAG 引擎    │  │  關聯分析    │  │  資料匯入    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    資料存取 Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  向量檢索    │  │  關聯索引    │  │  檔案讀取    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    資料儲存 Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  向量資料庫  │  │  Metadata DB │  │  原始檔案    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 技術選型

### 前端技術

#### 選項評估

| 技術 | 優點 | 缺點 | 評分 |
|------|------|------|------|
| **Electron** | 成熟穩定、生態豐富、Web 技術棧 | 體積大、效能較差 | ⭐⭐⭐⭐ |
| **Tauri** | 輕量、效能好、安全性高 | 生態較新、學習曲線 | ⭐⭐⭐⭐⭐ |
| **Qt (PyQt/PySide)** | 原生體驗、跨平台 | Python 打包困難 | ⭐⭐⭐ |
| **WPF (.NET)** | Windows 原生、效能好 | 僅限 Windows | ⭐⭐⭐ |

#### 建議選擇：**Tauri** ✅

**理由**：
- 輕量級（<10MB vs Electron 的 50-100MB）
- 使用 Web 前端技術（React/Vue/Svelte）
- Rust 後端提供高效能
- 符合「離線優先」需求
- 良好的安全性

**前端框架**：Svelte 或 React
- Svelte：更輕量、編譯時優化
- React：生態更豐富、組件多

### 後端/核心技術

#### 語言選擇

| 語言 | 優點 | 缺點 | 適用性 |
|------|------|------|--------|
| **Python** | AI/ML 生態豐富、快速開發 | 效能較差、打包困難 | ⭐⭐⭐⭐⭐ |
| **Rust** | 高效能、記憶體安全 | 學習曲線陡峭 | ⭐⭐⭐⭐ |
| **Node.js** | 與前端統一技術棧 | AI 生態較弱 | ⭐⭐⭐ |

#### 建議選擇：**Python (核心邏輯) + Rust (效能關鍵路徑)** ✅

**混合架構**：
- Python：RAG 引擎、LLM 整合、資料處理
- Rust：向量檢索、檔案索引、效能關鍵模組

### 向量資料庫

#### 選項評估

| 資料庫 | 類型 | 優點 | 缺點 | 評分 |
|--------|------|------|------|------|
| **Chroma** | 嵌入式 | 簡單、輕量、Python 整合好 | 功能較少 | ⭐⭐⭐⭐⭐ |
| **FAISS** | 函式庫 | Meta 出品、效能極佳 | 需自行管理持久化 | ⭐⭐⭐⭐ |
| **Qdrant** | 伺服器 | 功能完整、可擴展 | 需要額外伺服器 | ⭐⭐⭐ |
| **Milvus** | 伺服器 | 企業級、功能強大 | 過於複雜、重量級 | ⭐⭐ |

#### 建議選擇：**Chroma** ✅

**理由**：
- 嵌入式資料庫，無需額外伺服器
- Python API 簡潔易用
- 自動持久化
- 支援 filter 與 metadata 查詢
- 適合桌面應用的規模

### LLM 整合

#### 選項評估

**本機模型**：
- Ollama（推薦）- 易於安裝與管理
- llama.cpp - 輕量級推理引擎
- GPT4All - 多模型支援

**API 服務**：
- OpenAI API - 效果最好但需連網
- Anthropic Claude - 長文本能力強
- 本地私有部署（如 vLLM）

#### 建議選擇：**Ollama (本機) + OpenAI API (可選)** ✅

**理由**：
- Ollama 提供簡單的模型管理
- 支援多種開源模型（Llama, Mistral, Phi 等）
- 可選擇性啟用 API（使用者配置）
- 符合「離線優先，選擇性連網」的需求

### OCR 引擎

#### 選項評估

| 引擎 | 語言支援 | 準確度 | 授權 | 評分 |
|------|----------|--------|------|------|
| **Tesseract** | 繁中/英 | 中 | Apache 2.0 | ⭐⭐⭐⭐ |
| **PaddleOCR** | 繁中/英 | 高 | Apache 2.0 | ⭐⭐⭐⭐⭐ |
| **EasyOCR** | 多語言 | 中 | Apache 2.0 | ⭐⭐⭐⭐ |

#### 建議選擇：**PaddleOCR** ✅

**理由**：
- 中文辨識準確度高
- 支援繁體中文與英文
- 開源且活躍維護
- 可離線使用

---

## 資料流程

### 1. 資料匯入流程

```
使用者選擇資料夾
       ↓
掃描檔案系統（MD, JPG）
       ↓
解析 Markdown 檔案
  ├─ 提取 Frontmatter
  ├─ 解析 Wikilink
  ├─ 提取標籤
  └─ 分段（Chunking）
       ↓
處理圖片（OCR）
  ├─ 文字提取
  └─ 儲存到 Metadata
       ↓
向量化（Embedding）
       ↓
儲存到向量資料庫
       ↓
建立關聯索引
```

### 2. RAG 查詢流程

```
使用者提問
       ↓
問題向量化
       ↓
向量相似度檢索（Top-K）
       ↓
Reranking（可選）
       ↓
擷取相關片段
       ↓
構建 Prompt
  ├─ 系統提示詞
  ├─ 檢索到的內容
  └─ 使用者問題
       ↓
LLM 生成回答
       ↓
附加來源資訊
       ↓
回傳給使用者
```

### 3. 關聯分析流程

```
選擇目標文件
       ↓
提取關鍵詞（TF-IDF）
       ↓
計算向量相似度
       ↓
混合評分
  ├─ 關鍵詞共現：40%
  ├─ 向量相似度：40%
  └─ 手動連結：20%
       ↓
過濾閾值
       ↓
構建圖譜資料
       ↓
視覺化渲染
```

---

## 資料模型

### 文件 (Document)

```python
class Document:
    id: str                    # 唯一識別碼
    path: str                  # 檔案路徑
    filename: str              # 檔名
    title: str                 # 標題（從 frontmatter 或首行）
    content: str               # 原始內容
    content_hash: str          # 內容雜湊（用於檢測變更）
    tags: List[str]            # 標籤
    created_at: datetime       # 建立時間
    updated_at: datetime       # 更新時間
    metadata: Dict             # 其他元數據
    source_folder: str         # 來源資料夾
```

### 文件片段 (Chunk)

```python
class Chunk:
    id: str                    # 唯一識別碼
    document_id: str           # 所屬文件
    content: str               # 片段內容
    embedding: List[float]     # 向量
    start_line: int            # 起始行號
    end_line: int              # 結束行號
    chunk_index: int           # 在文件中的順序
    metadata: Dict             # 繼承自文件的 metadata
```

### 關聯 (Relationship)

```python
class Relationship:
    source_doc_id: str         # 來源文件
    target_doc_id: str         # 目標文件
    score: float               # 關聯強度 (0-1)
    type: str                  # 關聯類型（關鍵詞/向量/手動）
    keywords: List[str]        # 共同關鍵詞
    created_at: datetime       # 建立時間
```

---

## 核心演算法

### 1. 文件分塊策略

#### 策略 A：固定大小（簡單但可能斷句）
```python
chunk_size = 500  # 字元數
overlap = 50      # 重疊區域
```

#### 策略 B：語意分塊（較佳，基於段落或標題）✅
```python
def semantic_chunking(content: str) -> List[str]:
    # 1. 按 Markdown 標題分割
    sections = split_by_headers(content)
    
    # 2. 過長的段落再分割
    chunks = []
    for section in sections:
        if len(section) > MAX_CHUNK_SIZE:
            chunks.extend(split_by_sentences(section))
        else:
            chunks.append(section)
    
    return chunks
```

### 2. 混合檢索策略

結合關鍵詞檢索與向量檢索：

```python
def hybrid_search(query: str, top_k: int = 10) -> List[Chunk]:
    # 1. 向量檢索
    vector_results = vector_db.search(
        embedding=embed(query),
        top_k=top_k * 2
    )
    
    # 2. 關鍵詞檢索（BM25）
    keyword_results = bm25_search(query, top_k=top_k * 2)
    
    # 3. 合併與重排
    combined = merge_and_rerank(
        vector_results,
        keyword_results,
        weights=[0.6, 0.4]  # 向量 60%, 關鍵詞 40%
    )
    
    return combined[:top_k]
```

### 3. 關聯評分演算法

```python
def calculate_relationship_score(doc_a: Document, doc_b: Document) -> float:
    # 1. 關鍵詞共現分數
    keywords_a = extract_keywords(doc_a.content)
    keywords_b = extract_keywords(doc_b.content)
    keyword_score = jaccard_similarity(keywords_a, keywords_b)
    
    # 2. 向量相似度
    vector_score = cosine_similarity(
        doc_a.embedding,
        doc_b.embedding
    )
    
    # 3. 手動連結加成
    manual_link_score = 1.0 if has_wikilink(doc_a, doc_b) else 0.0
    
    # 4. 混合評分
    final_score = (
        keyword_score * 0.3 +
        vector_score * 0.5 +
        manual_link_score * 0.2
    )
    
    return final_score
```

---

## 效能考量

### 1. 索引效能

- **增量索引**：只處理新增/修改的檔案
- **平行處理**：使用多執行緒處理檔案
- **批次嵌入**：批次呼叫 embedding 模型

### 2. 查詢效能

- **快取機制**：快取常見問題的結果
- **預過濾**：使用 metadata 預先過濾候選文件
- **懶載入**：僅在需要時載入完整文件內容

### 3. 記憶體管理

- **串流處理**：大型檔案使用串流讀取
- **分頁載入**：向量資料庫結果分頁
- **資源釋放**：及時釋放不需要的資源

---

## 安全性考量

### 1. 資料隱私

- ✅ 所有資料儲存在本機
- ✅ 敏感資料不上傳到外部
- ✅ API 金鑰加密儲存

### 2. 程式碼安全

- ✅ 輸入驗證（防止路徑遍歷）
- ✅ 沙箱執行（限制檔案存取）
- ✅ 依賴安全掃描

---

## 部署與打包

### Windows 打包流程

```bash
# 1. 建置前端
cd frontend
npm run build

# 2. 打包 Tauri 應用
npm run tauri build

# 3. 產生安裝程式
# 輸出：target/release/bundle/msi/AI知識++_1.0.0_x64_en-US.msi
```

### 安裝包內容

```
AI知識++/
├── app.exe                   # 主程式
├── resources/
│   ├── models/              # 預設 LLM 模型（可選）
│   └── assets/              # 資源檔案
├── config/
│   └── default.toml         # 預設配置
└── README.txt               # 安裝說明
```

---

## 開發環境設置

### 必要工具

- Node.js 18+
- Python 3.10+
- Rust 1.70+
- Ollama（用於本機 LLM）

### 開發指令

```bash
# 安裝前端依賴
cd frontend && npm install

# 安裝後端依賴
cd backend && pip install -r requirements.txt

# 開發模式執行
npm run tauri dev

# 執行測試
npm test
pytest
```

---

## 後續優化方向

### V2 潛在改進

- **多格式支援**：PDF, DOCX, PPTX
- **即時同步**：檔案系統監控
- **進階圖譜**：時間軸、分類視圖
- **協作功能**：多人共享知識庫
- **行動版**：iOS/Android 支援

---

**最後更新**：2026-02-17
