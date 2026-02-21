# AI知識++ 使用指南

歡迎使用 AI知識++，一個本機運作的私人知識庫系統！

## 目錄

- [快速開始](#快速開始)
- [基本概念](#基本概念)
- [常見工作流程](#常見工作流程)
- [進階功能](#進階功能)
- [最佳實踐](#最佳實踐)
- [常見問題](#常見問題)

## 快速開始

### 1. 安裝

請參考 [INSTALL.md](INSTALL.md) 完成系統安裝。

### 2. 索引你的知識庫

```bash
ai-knowledge index /path/to/your/obsidian/vault
```

系統會掃描指定資料夾中的所有 Markdown 文件，建立向量索引。

### 3. 開始提問

```bash
ai-knowledge search "什麼是 Rust 所有權？"
```

系統會搜尋相關文件並提供答案，同時附上來源引用。

### 4. 互動式對話

```bash
ai-knowledge chat
```

進入互動模式，可以進行多輪對話，系統會記住上下文。

## 基本概念

### 知識庫結構

AI知識++ 支援 Obsidian 格式的 Markdown 文件：

- **Wikilinks**: `[[文件名]]` 或 `[[文件名|顯示文字]]`
- **Tags**: `#標籤` 或 `#巢狀/標籤`
- **Frontmatter**: YAML 格式的文件元資料
- **圖片**: 支援 OCR 文字擷取（需啟用）

### 資料儲存

- **向量資料庫**: `./data/chroma_db/` - 儲存文件嵌入向量
- **對話紀錄**: `./data/conversations/` - 儲存聊天會話
- **快取**: `./data/cache/` - 嵌入快取，加速處理

### 工作原理

1. **索引階段**: 
   - 掃描 Markdown 文件
   - 切分為語義區塊（chunks）
   - 生成向量嵌入
   - 建立關係圖

2. **查詢階段**:
   - 將問題轉換為向量
   - 搜尋最相關的區塊
   - 使用 LLM 生成答案
   - 附上來源引用

## 常見工作流程

### 工作流程 1：建立新知識庫

```bash
# 1. 索引你的筆記
ai-knowledge index ~/Documents/MyNotes

# 2. 查看統計資訊
ai-knowledge stats

# 3. 測試搜尋
ai-knowledge search "測試查詢"
```

### 工作流程 2：更新現有知識庫

```bash
# 強制重新索引（當文件有更新時）
ai-knowledge index ~/Documents/MyNotes --force

# 查看更新後的統計
ai-knowledge stats
```

### 工作流程 3：互動式研究

```bash
# 啟動對話模式
ai-knowledge chat

# 在對話中：
You: 什麼是 Rust 所有權？
Assistant: [提供答案並附來源]

You: 能舉個例子嗎？
Assistant: [根據上下文提供範例]

You: exit  # 結束對話
```

### 工作流程 4：知識圖譜視覺化

```bash
# 生成 D3.js 格式的圖譜
ai-knowledge graph output/graph.json --format d3

# 生成 Mermaid 格式（可嵌入 Markdown）
ai-knowledge graph output/graph.md --format mermaid

# 限制節點數量
ai-knowledge graph output/graph.json --format d3 --max-nodes 30
```

### 工作流程 5：資料庫備份與遷移

```bash
# 匯出整個知識庫
ai-knowledge export backup.zip --archive

# 在另一台電腦上匯入
ai-knowledge import backup.zip --verify

# 驗證來源資料夾
ai-knowledge verify
```

## 進階功能

### 啟用 OCR（圖片文字擷取）

```bash
# 索引時啟用 OCR
ai-knowledge index /path/to/vault --ocr
```

**注意**: OCR 需要安裝 PaddleOCR 依賴（參考 INSTALL.md）。

### 多資料夾索引

```bash
# 同時索引多個資料夾
ai-knowledge index /path/vault1 /path/vault2 /path/vault3
```

### 會話管理

```bash
# 使用特定會話 ID
ai-knowledge chat --session my-research-session

# 稍後繼續相同會話
ai-knowledge chat --session my-research-session
```

### 詳細統計資訊

```bash
# 查看詳細配置
ai-knowledge stats --detailed
```

### 自訂搜尋參數

```bash
# 限制結果數量
ai-knowledge search "查詢" --limit 3

# 設定最小相關度分數
ai-knowledge search "查詢" --min-score 0.5
```

## 最佳實踐

### 1. 組織你的筆記

- 使用清晰的標題和結構
- 添加相關的標籤（tags）
- 使用 wikilinks 連接相關文件
- 在 frontmatter 中添加元資料

**範例**:
```markdown
---
title: Rust 所有權
author: Your Name
tags: [rust, programming, memory]
created: 2024-01-01
---

# Rust 所有權

所有權是 Rust 最獨特的功能...

參考：[[記憶體管理]] [[Rust 入門]]
```

### 2. 定期更新索引

當你的筆記有大量更新時：

```bash
ai-knowledge index /path/to/vault --force
```

### 3. 備份策略

建議定期備份：

```bash
# 每週備份
ai-knowledge export backups/backup-$(date +%Y%m%d).zip --archive
```

### 4. 查詢技巧

- **具體問題**: "Rust 的三個所有權規則是什麼？"
- **概念查詢**: "解釋 Rust 所有權的概念"
- **比較查詢**: "Rust 和 C++ 的記憶體管理有什麼不同？"
- **摘要請求**: "總結 Rust 的主要特點"

### 5. 利用對話上下文

在 chat 模式中，系統會記住上下文：

```
You: 什麼是 Rust？
Assistant: [解釋 Rust]

You: 它的主要優點是什麼？  # 系統知道"它"指的是 Rust
Assistant: [列出 Rust 優點]

You: 給我看一個範例  # 繼續相關話題
Assistant: [提供 Rust 範例]
```

## 常見問題

### Q: 支援哪些文件格式？

A: 目前主要支援 Markdown（.md）文件。圖片可透過 OCR 擷取文字（需啟用）。

### Q: 可以索引多大的知識庫？

A: 系統可以處理數千個文件。實際限制取決於硬體（特別是記憶體）。

### Q: 如何處理中文內容？

A: 系統原生支援中英混合內容，無需額外配置。

### Q: 搜尋結果不準確怎麼辦？

A: 
1. 確保文件已正確索引
2. 嘗試更具體的問題
3. 調整 `--min-score` 參數
4. 重新索引: `ai-knowledge index /path --force`

### Q: 可以離線使用嗎？

A: 是的！所有資料和處理都在本機進行，無需網路連線。

### Q: 如何更新系統？

A: 拉取最新程式碼後，重新安裝依賴：
```bash
cd apps/issue-3
pip install -r requirements.txt --upgrade
```

### Q: 資料儲存在哪裡？

A: 
- 原始筆記：保持在原位置（只讀）
- 向量索引：`./data/chroma_db/`
- 對話記錄：`./data/conversations/`
- 快取：`./data/cache/`

### Q: 如何刪除索引重新開始？

A: 刪除資料目錄：
```bash
rm -rf ./data/chroma_db
rm -rf ./data/cache
ai-knowledge index /path/to/vault
```

### Q: 支援即時同步嗎？

A: 目前需要手動重新索引。可使用 `--force` 選項更新。

### Q: 可以同時使用多個知識庫嗎？

A: 可以索引多個資料夾到同一個向量資料庫，或為不同專案使用不同的資料目錄。

## 下一步

- 閱讀 [CLI_REFERENCE.md](CLI_REFERENCE.md) 了解所有命令的詳細說明
- 查看 [API_REFERENCE.md](API_REFERENCE.md) 學習如何在 Python 中使用
- 遇到問題？參考 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 支援與回饋

如果你遇到問題或有改進建議，請：

1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. 檢查 GitHub Issues
3. 提交新 Issue

祝你使用愉快！ 🎉
