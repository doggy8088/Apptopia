# AI知識++ CLI 命令參考

完整的命令列介面參考文件。

## 總覽

```bash
ai-knowledge [OPTIONS] COMMAND [ARGS]...
```

## 全域選項

- `--version`: 顯示版本資訊
- `--help`: 顯示幫助訊息

## 命令列表

1. [index](#index) - 索引資料夾
2. [search](#search) - 搜尋知識庫
3. [chat](#chat) - 互動式對話
4. [stats](#stats) - 顯示統計資訊
5. [export](#export) - 匯出資料庫
6. [import](#import) - 匯入資料庫
7. [graph](#graph) - 生成知識圖譜
8. [verify](#verify) - 驗證來源資料夾

---

## index

索引 Obsidian 資料夾到知識庫。

### 語法

```bash
ai-knowledge index PATH [PATH...] [OPTIONS]
```

### 參數

- `PATH`: 一個或多個要索引的資料夾路徑（必需）

### 選項

- `--force`: 強制重新索引所有文件
- `--ocr`: 啟用 OCR 功能處理圖片

### 範例

```bash
# 索引單一資料夾
ai-knowledge index ~/Documents/MyNotes

# 索引多個資料夾
ai-knowledge index ~/Notes ~/Work

# 強制重新索引
ai-knowledge index ~/Notes --force
```

---

## search

搜尋知識庫並獲取答案。

### 語法

```bash
ai-knowledge search QUERY [OPTIONS]
```

### 參數

- `QUERY`: 搜尋查詢（必需）

### 選項

- `--limit INTEGER`: 最大結果數量（預設：5）
- `--min-score FLOAT`: 最小相關度分數（預設：0.3）

### 範例

```bash
ai-knowledge search "什麼是 Rust 所有權？"
ai-knowledge search "Python" --limit 3 --min-score 0.5
```

---

## chat

啟動互動式聊天模式。

### 語法

```bash
ai-knowledge chat [OPTIONS]
```

### 選項

- `--session TEXT`: 會話 ID

### 範例

```bash
ai-knowledge chat
ai-knowledge chat --session my-research
```

---

## stats

顯示知識庫統計資訊。

### 語法

```bash
ai-knowledge stats [OPTIONS]
```

### 選項

- `--detailed`: 顯示詳細資訊

### 範例

```bash
ai-knowledge stats
ai-knowledge stats --detailed
```

---

## export

匯出知識庫到檔案。

### 語法

```bash
ai-knowledge export OUTPUT [OPTIONS]
```

### 參數

- `OUTPUT`: 輸出路徑（必需）

### 選項

- `--archive`: 建立 ZIP 壓縮檔

### 範例

```bash
ai-knowledge export backup.zip --archive
ai-knowledge export ./backup
```

---

## import

從匯出檔案匯入知識庫。

### 語法

```bash
ai-knowledge import SOURCE [OPTIONS]
```

### 參數

- `SOURCE`: 匯入來源路徑（必需）

### 選項

- `--verify`: 匯入後驗證來源資料夾

### 範例

```bash
ai-knowledge import backup.zip
ai-knowledge import backup.zip --verify
```

---

## graph

生成知識圖譜視覺化。

### 語法

```bash
ai-knowledge graph OUTPUT [OPTIONS]
```

### 參數

- `OUTPUT`: 輸出檔案路徑（必需）

### 選項

- `--format CHOICE`: 輸出格式（d3, mermaid, obsidian, graphml）
- `--max-nodes INTEGER`: 最大節點數量（預設：50）

### 範例

```bash
ai-knowledge graph graph.json --format d3
ai-knowledge graph graph.md --format mermaid --max-nodes 30
```

---

## verify

驗證來源資料夾可用性。

### 語法

```bash
ai-knowledge verify [FOLDERS...]
```

### 參數

- `FOLDERS`: 要驗證的資料夾（可選）

### 範例

```bash
ai-knowledge verify
ai-knowledge verify ~/Notes ~/Work
```

---

## 環境變數

- `AI_KNOWLEDGE_DATA_DIR`: 自訂資料目錄
- `AI_KNOWLEDGE_CACHE_DIR`: 自訂快取目錄

## 設定檔

預設設定位置：`~/.ai-knowledge/config.yaml`

範例設定：

```yaml
chroma_path: ./data/chroma_db
conversation_path: ./data/conversations
cache_dir: ./data/cache
```

## 退出碼

- `0`: 成功
- `1`: 錯誤

