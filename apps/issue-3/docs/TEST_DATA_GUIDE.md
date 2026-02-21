# 測試資料集說明

## 概述

本專案使用從 Issue #3 討論中提供的 Obsidian 筆記資料作為測試資料集。這是一個真實的知識庫範例，涵蓋程式設計、AI 工具、數學等多個領域的學習筆記。

**資料來源**：[Obsidian-Note-Card-example.zip](https://github.com/user-attachments/files/25368336/Obsidian-Note-Card-example.zip)

---

## 資料統計

### 檔案統計

- **總大小**：26 MB
- **Markdown 文件**：43 個
- **圖片檔案**：74 個（JPG, PNG）
- **其他檔案**：Obsidian 設定檔、索引檔等

### 目錄結構

```
test-data/
├── .obsidian/                 # Obsidian 設定（不納入處理）
│   ├── plugins/
│   ├── snippets/
│   └── themes/
├── .smart-env/                # Smart Connections 外掛資料（不納入處理）
│   ├── embedding_models/
│   ├── event_logs/
│   ├── multi/
│   ├── smart_components/
│   └── smart_contexts/
├── Atlas地圖集/               # 知識地圖
│   └── MOC/                   # Map of Content（內容地圖）
│       ├── C++ MOC.md
│       ├── Rust MOC.md
│       ├── Zig MOC.md
│       └── ...
├── Card卡片盒/                # 主要學習筆記
│   └── 學習/
│       ├── AI/                # AI 工具與應用
│       ├── 其他/              # 其他主題
│       ├── 數學/              # 數學概念
│       ├── 程式/              # 程式設計
│       │   ├── C++/
│       │   ├── CSharp/
│       │   ├── Docker/
│       │   ├── JS_TS/
│       │   ├── Kotlin_Java/
│       │   ├── Python/
│       │   ├── Rust/          # 最多內容
│       │   ├── Zig/
│       │   └── 後端/
│       ├── 筆記術/            # 筆記方法論
│       └── 美術/              # 設計相關
└── Source來源筆記/            # 參考來源
    └── 圖片/                  # 插圖與截圖
```

---

## 內容分析

### Rust 筆記（最豐富的主題）

位於 `Card卡片盒/學習/程式/Rust/` 目錄，包含以下主題：

1. **基礎概念**
   - Rust 語言基本.md
   - Rust 所有權.md
   - Rust 引用.md
   - Slice 切片.md

2. **資料類型**
   - Rust String.md
   - Rust Vector.md
   - Rust HashMap.md
   - Rust Enum枚舉.md
   - Rust Struct.md

3. **進階特性**
   - Rust 泛型.md
   - Rust std標準庫 Trait.md
   - Rust match & if let.md
   - Rust Type別名.md
   - Rust 屬性 Attributes.md

4. **實用主題**
   - Rust 測試.md
   - Rust 錯誤訊息.md
   - Rust 利用 Drop來保護邏輯.md

**為什麼 Rust 筆記最適合作為測試資料？**
- 概念之間有明確的關聯性（如：所有權 ↔ 引用）
- 內容結構化且完整
- 包含程式碼範例
- 適合測試跨文件檢索與關聯分析

### AI 工具筆記

位於 `Card卡片盒/學習/AI/` 目錄，包含：

- ChatGPT 相關
  - ChatGPT 指令大全
  - ChatGPT AI 翻譯工具
- 算圖工具
  - Stable Diffusion 架設教學
  - Lama Cleaner 開源AI修圖
  - 微軟 Bing AI繪圖工具
  - StockAI 圖片搜索引擎
- 工具集合
  - AI 工具百寶箱
  - 10個AI工具讓賺錢&工作效率翻100倍

### 其他主題

- **數學**：向量相關概念
- **筆記術**：Zettelkasten、Obsidian 使用技巧
- **美術**：設計工具與資源
- **後端**：伺服器、資料庫相關

---

## Obsidian 特殊語法範例

根據初步檢視，測試資料使用了以下 Obsidian 語法：

### 1. 內部連結（Wikilinks）

```markdown
[[Rust 所有權]]
[[Rust String|字串類型]]
[[Rust Enum枚舉#Pattern Matching]]
```

### 2. 標籤

```markdown
#rust #programming #ownership
#ai/tools #chatgpt
```

### 3. YAML Frontmatter

```yaml
---
title: Rust 所有權
tags: [rust, ownership, memory]
created: 2024-01-15
---
```

### 4. Callouts

```markdown
> [!note] 重要概念
> 這是一個重要的筆記

> [!warning] 注意事項
> 需要特別注意的地方
```

### 5. 任務清單

```markdown
- [x] 已完成的任務
- [ ] 待完成的任務
```

---

## 資料品質評估

### 優點

✅ **真實場景**：實際使用者的筆記，不是人工構造的測試資料  
✅ **多樣性**：涵蓋多個領域與主題  
✅ **結構化**：使用 Obsidian 的組織方式，有明確的層級  
✅ **關聯性**：文件之間有內部連結，適合測試圖譜功能  
✅ **中文為主**：符合目標使用者（繁體中文使用者）  

### 限制

⚠️ **Rust 偏重**：大部分內容集中在 Rust，其他主題較少  
⚠️ **圖片說明不足**：許多圖片缺乏上下文或替代文字  
⚠️ **內容深度不一**：有些文件內容豐富，有些較簡略  
⚠️ **外掛依賴**：包含 Smart Connections 等外掛產生的檔案  

---

## 測試場景設計

基於這個資料集，我們可以設計以下測試場景：

### 場景 1：單一主題深度查詢（Rust）

**適用測試**：
- 基本問答（Q1-Q5）
- 摘要生成（Q14）
- 關聯分析

**範例問題**：
- 「Rust 的所有權規則是什麼？」
- 「如何在 Rust 中使用 HashMap？」
- 「Vector 和 Slice 有什麼關係？」

### 場景 2：跨主題查詢（AI 工具）

**適用測試**：
- 跨文件關聯（Q6-Q10）
- 主題摘要（Q15）

**範例問題**：
- 「有哪些 AI 繪圖工具？」
- 「ChatGPT 可以用來做什麼？」
- 「如何使用 Stable Diffusion？」

### 場景 3：未命中測試

**適用測試**：
- 本機未命中（Q11-Q13）

**範例問題**：
- 「Python 的 asyncio 如何使用？」（無此資料）
- 「React 的 Hooks 有哪些？」（無此資料）

### 場景 4：知識圖譜測試

**適用測試**：
- 關聯強度計算
- 圖譜視覺化

**預期關聯**：
- Rust 所有權 ↔ Rust 引用（高度相關）
- Rust Vector ↔ Slice 切片（高度相關）
- Rust Enum ↔ Rust match（高度相關）
- Rust MOC ↔ 各 Rust 子主題（中度相關）

---

## 資料處理注意事項

### 需要排除的內容

- `.obsidian/` 目錄（Obsidian 設定）
- `.smart-env/` 目錄（外掛資料）
- `.gitignore` 檔案

### 需要特別處理的內容

- **中文檔名**：確保系統正確處理 UTF-8 編碼
- **內部連結**：需要解析 `[[]]` 語法並建立文件間連結
- **標籤**：提取 `#tag` 並建立標籤索引
- **圖片路徑**：相對路徑需要正確解析

---

## 擴展建議

為了更全面的測試，建議後續補充：

1. **PDF 文件**：測試 PDF 解析功能（V2）
2. **更多主題**：增加不同領域的筆記
3. **英文內容**：測試多語言支援
4. **大型文件**：測試效能邊界
5. **複雜格式**：表格、數學公式等

---

## 使用方式

### 開發環境

```bash
# 資料位置
cd apps/issue-3/data/test-data

# 統計文件數量
find . -type f -name "*.md" | wc -l

# 檢視某個文件
cat "Card卡片盒/學習/程式/Rust/Rust 所有權.md"
```

### 測試腳本（待開發）

```python
# 範例：載入測試資料
from pathlib import Path

TEST_DATA_DIR = Path("apps/issue-3/data/test-data")

def load_test_documents():
    """載入所有 Markdown 文件"""
    md_files = list(TEST_DATA_DIR.rglob("*.md"))
    # 排除 .obsidian 和 .smart-env
    md_files = [
        f for f in md_files 
        if not any(p.startswith('.') for p in f.parts)
    ]
    return md_files
```

---

## 致謝

感謝原始資料提供者分享真實的 Obsidian 知識庫作為測試資料，這對專案開發非常有幫助。

---

**最後更新**：2026-02-17  
**資料版本**：1.0  
**資料來源日期**：2026-02-14
