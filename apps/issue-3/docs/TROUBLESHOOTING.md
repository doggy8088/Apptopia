# AI知識++ 疑難排解指南

本文件列出常見問題及其解決方案。

## 目錄

- [安裝問題](#安裝問題)
- [索引問題](#索引問題)
- [搜尋問題](#搜尋問題)
- [效能問題](#效能問題)
- [資料庫問題](#資料庫問題)
- [其他問題](#其他問題)

## 安裝問題

### Q: pip 安裝依賴失敗

**症狀**: `pip install -r requirements.txt` 出現錯誤

**解決方案**:

```bash
# 1. 升級 pip
python -m pip install --upgrade pip

# 2. 清除快取
pip cache purge

# 3. 重新安裝
pip install -r requirements.txt --no-cache-dir

# 4. 如仍失敗，逐一安裝
pip install chromadb
pip install sentence-transformers
# ... 其他套件
```

### Q: Python 版本不相容

**症狀**: 提示需要 Python 3.10+

**解決方案**:

```bash
# 檢查版本
python --version

# 安裝正確版本
# Windows: 從 python.org 下載
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11
```

### Q: ChromaDB 安裝錯誤

**症狀**: ChromaDB 相關的編譯錯誤

**解決方案**:

```bash
# macOS
xcode-select --install
pip install chromadb

# Linux
sudo apt install build-essential
pip install chromadb

# Windows
# 使用預編譯的 wheel
pip install chromadb --prefer-binary
```

### Q: 記憶體不足錯誤

**症狀**: 安裝過程中出現 MemoryError

**解決方案**:

```bash
# 增加虛擬記憶體（swap）
# 或逐一安裝較大的套件
pip install torch --no-cache-dir
pip install sentence-transformers --no-cache-dir
```

## 索引問題

### Q: 索引速度很慢

**症狀**: 處理大量文件時索引緩慢

**解決方案**:

1. **檢查硬體**:
   - 使用 SSD 而非 HDD
   - 確保有足夠 RAM（建議 8GB+）

2. **調整批次大小**（在程式碼中）:
   ```python
   # 修改 processor.py
   batch_size = 10  # 降低批次大小
   ```

3. **使用快取**:
   ```bash
   # 不要每次都 --force
   ai-knowledge index ~/Notes  # 只處理新/改動的文件
   ```

### Q: 某些文件沒被索引

**症狀**: 搜尋時找不到特定文件

**解決方案**:

1. **檢查檔案格式**:
   - 只支援 `.md` 檔案
   - 檢查編碼是否為 UTF-8

2. **檢查檔案內容**:
   ```bash
   # 檢查檔案
   cat file.md
   # 確認不是空檔案
   ```

3. **強制重新索引**:
   ```bash
   ai-knowledge index ~/Notes --force
   ```

4. **查看處理日誌**:
   - 檢查是否有錯誤訊息
   - 確認檔案路徑正確

### Q: OCR 不工作

**症狀**: 圖片中的文字沒被擷取

**解決方案**:

1. **確認 OCR 已安裝**:
   ```bash
   pip install paddleocr paddlepaddle opencv-python Pillow
   ```

2. **首次使用需下載模型**:
   - 需要網路連線
   - 會自動下載約 200MB 模型
   - 等待下載完成

3. **檢查圖片格式**:
   - 支援：PNG, JPG, JPEG
   - 圖片應包含清晰的文字

4. **手動啟用 OCR**:
   ```bash
   ai-knowledge index ~/Notes --ocr
   ```

### Q: 解析錯誤

**症狀**: 某些 Markdown 語法無法正確解析

**解決方案**:

1. **檢查支援的語法**: 參考 `docs/OBSIDIAN_SYNTAX_SUPPORT.md`

2. **簡化問題檔案**:
   - 移除複雜的巢狀結構
   - 檢查是否有格式錯誤

3. **提交 Issue**:
   - 如果是不支援的語法
   - 提供範例檔案

## 搜尋問題

### Q: 搜尋沒有結果

**症狀**: 明明有相關文件但搜尋不到

**解決方案**:

1. **降低相關度門檻**:
   ```bash
   ai-knowledge search "查詢" --min-score 0.1
   ```

2. **增加結果數量**:
   ```bash
   ai-knowledge search "查詢" --limit 10
   ```

3. **使用不同的關鍵字**:
   - 嘗試同義詞
   - 使用更具體或更寬泛的詞彙

4. **確認已索引**:
   ```bash
   ai-knowledge stats
   # 檢查 Total Chunks 數量
   ```

5. **重新索引**:
   ```bash
   ai-knowledge index ~/Notes --force
   ```

### Q: 搜尋結果不準確

**症狀**: 回答與問題不相關

**解決方案**:

1. **提高相關度門檻**:
   ```bash
   ai-knowledge search "查詢" --min-score 0.5
   ```

2. **使用更具體的問題**:
   - 不佳: "Rust"
   - 較好: "Rust 的所有權規則是什麼？"

3. **檢查文件品質**:
   - 確保文件內容完整
   - 使用清晰的標題和結構

### Q: 回答是英文但我問中文

**症狀**: 語言不匹配

**解決方案**:

- 目前使用 MockLLMClient，回答可能不考慮語言
- 整合真實 LLM（OpenAI, Ollama）可改善
- 確保文件也使用相同語言

### Q: 沒有來源引用

**症狀**: 回答沒有附上來源

**解決方案**:

1. **檢查是否有找到相關資料**:
   - 如果 `has_local_data` 為 False，就不會有來源

2. **降低相關度門檻**:
   ```bash
   ai-knowledge search "查詢" --min-score 0.2
   ```

## 效能問題

### Q: 系統回應緩慢

**症狀**: 查詢需要很長時間

**解決方案**:

1. **檢查資料量**:
   ```bash
   ai-knowledge stats --detailed
   ```

2. **減少索引大小**:
   - 只索引需要的資料夾
   - 移除不重要的文件

3. **使用 SSD**:
   - 向量資料庫在 SSD 上效能更好

4. **增加記憶體**:
   - 建議至少 8GB RAM

5. **清除快取**:
   ```bash
   rm -rf ./data/cache
   ```

### Q: 記憶體使用過高

**症狀**: 系統記憶體不足

**解決方案**:

1. **關閉不必要的應用程式**

2. **調整批次大小**（在程式碼中）

3. **分批處理**:
   ```bash
   # 分別索引不同資料夾
   ai-knowledge index ~/Notes/Part1
   ai-knowledge index ~/Notes/Part2
   ```

### Q: 硬碟空間不足

**症狀**: 無法建立索引

**解決方案**:

1. **清理舊資料**:
   ```bash
   # 刪除舊的對話記錄
   rm -rf ./data/conversations/*
   
   # 清除快取
   rm -rf ./data/cache
   ```

2. **壓縮資料庫** (ChromaDB 會自動壓縮)

3. **使用外部儲存**:
   - 將資料目錄移到較大的硬碟
   - 設定環境變數指向新位置

## 資料庫問題

### Q: 資料庫損壞

**症狀**: 無法讀取向量資料庫

**解決方案**:

```bash
# 1. 備份現有資料
cp -r ./data/chroma_db ./data/chroma_db.backup

# 2. 刪除損壞的資料庫
rm -rf ./data/chroma_db

# 3. 重新索引
ai-knowledge index ~/Notes --force
```

### Q: 匯出/匯入失敗

**症狀**: 無法完成資料庫遷移

**解決方案**:

1. **檢查磁碟空間**:
   - 確保有足夠空間建立壓縮檔

2. **檢查權限**:
   ```bash
   # 確保有寫入權限
   chmod -R u+w ./data
   ```

3. **分步驟操作**:
   ```bash
   # 先匯出不壓縮
   ai-knowledge export ./backup
   
   # 手動壓縮
   zip -r backup.zip ./backup
   ```

### Q: 來源驗證失敗

**症狀**: verify 命令顯示資料夾遺失

**解決方案**:

1. **確認路徑正確**:
   - 使用絕對路徑
   - 檢查資料夾是否存在

2. **更新資料夾位置**:
   - 如果資料夾移動了
   - 重新索引新位置

3. **接受凍結狀態**:
   - 如果來源確實不可用
   - 文件會標記為 "frozen"

## 其他問題

### Q: 對話沒有記住上下文

**症狀**: 多輪對話失效

**解決方案**:

1. **使用相同 session ID**:
   ```bash
   ai-knowledge chat --session my-session
   ```

2. **檢查對話是否儲存**:
   ```bash
   ls ./data/conversations/
   ```

3. **清除損壞的對話**:
   ```bash
   rm ./data/conversations/my-session.json
   ```

### Q: 圖譜生成失敗

**症狀**: graph 命令報錯

**解決方案**:

1. **確認有索引資料**:
   ```bash
   ai-knowledge stats
   ```

2. **減少節點數**:
   ```bash
   ai-knowledge graph output.json --max-nodes 20
   ```

3. **檢查輸出路徑**:
   - 確保目錄存在且可寫入

### Q: 權限錯誤

**症狀**: Permission denied

**解決方案**:

```bash
# macOS/Linux
sudo chown -R $USER:$USER /path/to/apps/issue-3

# 或使用 sudo 執行
sudo ai-knowledge index /path
```

### Q: 中文顯示亂碼

**症狀**: 終端機顯示問號或方塊

**解決方案**:

1. **設定終端機編碼為 UTF-8**

2. **Windows 用戶**:
   ```powershell
   # 設定 PowerShell 編碼
   $OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
   ```

3. **安裝適當的字型**:
   - 安裝支援中文的等寬字型
   - 如：Noto Sans CJK, Source Han Sans

### Q: 找不到命令

**症狀**: `ai-knowledge: command not found`

**解決方案**:

1. **使用完整路徑**:
   ```bash
   python /full/path/to/apps/issue-3/src/cli.py --help
   ```

2. **設定別名**:
   ```bash
   # 加到 ~/.bashrc 或 ~/.zshrc
   alias ai-knowledge="python /path/to/cli.py"
   ```

3. **建立符號連結**:
   ```bash
   sudo ln -s /path/to/cli.py /usr/local/bin/ai-knowledge
   chmod +x /path/to/cli.py
   ```

## 獲取更多幫助

如果問題仍未解決：

1. **查看日誌**: 執行時加上 `-v` 或 `--verbose` 選項（如果有）

2. **檢查 GitHub Issues**: 
   - 搜尋類似問題
   - 查看已知問題

3. **提交新 Issue**:
   - 描述問題
   - 提供錯誤訊息
   - 說明你的環境（OS, Python 版本等）
   - 列出已嘗試的解決方案

4. **查看原始碼**:
   - `src/backend/` - 後端實作
   - `src/cli.py` - CLI 實作
   - `tests/` - 測試範例

5. **執行測試**:
   ```bash
   pytest tests/ -v
   # 查看哪些測試失敗
   ```

## 調試技巧

### 啟用詳細輸出

```python
# 在 Python 程式中
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 檢查系統狀態

```bash
# 檢查 Python 環境
which python
python --version
pip list | grep -E "chroma|sentence"

# 檢查磁碟空間
df -h

# 檢查記憶體
free -h  # Linux
vm_stat  # macOS
```

### 隔離問題

1. 建立最小測試案例
2. 使用新的虛擬環境
3. 只索引少量文件測試

## 預防措施

- **定期備份**: 
  ```bash
  ai-knowledge export backups/backup-$(date +%Y%m%d).zip --archive
  ```

- **版本控制**: 記錄使用的版本

- **測試更新**: 在測試環境先試用新版本

- **文件品質**: 維護良好的筆記結構

---

**最後更新**: 2026-02-21
