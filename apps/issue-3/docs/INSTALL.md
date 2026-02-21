# AI知識++ 安裝指南

本文件說明如何在你的系統上安裝 AI知識++。

## 系統需求

### 最低需求

- **作業系統**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.10 或更高版本
- **記憶體**: 最少 4GB RAM（建議 8GB+）
- **硬碟空間**: 最少 2GB 可用空間
- **網路**: 初次安裝需要下載依賴套件

### 建議配置

- **記憶體**: 16GB RAM（處理大型知識庫時）
- **處理器**: 多核心 CPU（加速向量計算）
- **硬碟**: SSD（加快索引速度）

## 安裝步驟

### 1. 安裝 Python

確認 Python 版本：

```bash
python --version
# 或
python3 --version
```

如果版本低於 3.10，請從 [python.org](https://www.python.org/downloads/) 下載最新版本。

### 2. 克隆專案（開發模式）

```bash
git clone https://github.com/doggy8088/Apptopia.git
cd Apptopia/apps/issue-3
```

### 3. 建立虛擬環境（建議）

```bash
# 建立虛擬環境
python -m venv venv

# 啟用虛擬環境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 4. 安裝依賴套件

```bash
pip install -r requirements.txt
```

這會安裝所有必要的套件，包括：
- ChromaDB（向量資料庫）
- sentence-transformers（文本嵌入）
- click, rich（CLI 工具）
- networkx（圖形分析）
- 其他依賴

**安裝時間**: 首次安裝約需 5-15 分鐘，取決於網路速度。

### 5. 驗證安裝

```bash
# 測試 CLI 是否正常運作
python src/cli.py --version

# 或設定別名（方便使用）
alias ai-knowledge="python /path/to/apps/issue-3/src/cli.py"
```

### 6. 測試基本功能

```bash
# 執行測試
pytest tests/ -v

# 查看統計（第一次執行會初始化資料庫）
python src/cli.py stats
```

## 可選功能

### OCR 支援（圖片文字擷取）

如果需要從圖片中擷取文字，需要安裝額外的 OCR 依賴：

```bash
# 安裝 PaddleOCR 及相關套件
pip install paddleocr paddlepaddle opencv-python Pillow
```

**注意**: 
- PaddleOCR 首次使用會下載模型（約 200MB）
- GPU 版本需另外安裝 paddlepaddle-gpu
- 如不安裝，系統會自動使用 mock OCR（不影響基本功能）

### GPU 加速（可選）

如果你有 NVIDIA GPU，可以安裝 GPU 版本加速處理：

```bash
# 卸載 CPU 版本的 PyTorch
pip uninstall torch

# 安裝 GPU 版本（CUDA 11.8 範例）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 平台特定說明

### Windows

1. **長路徑支援**: 
   - 開啟「組策略編輯器」(gpedit.msc)
   - 啟用：電腦設定 > 系統管理範本 > 系統 > 檔案系統 > 「啟用 Win32 長路徑」

2. **執行權限**:
   - 可能需要以管理員身份執行 PowerShell
   - 或設定執行原則: `Set-ExecutionPolicy RemoteSigned`

3. **建立桌面捷徑**:
   ```powershell
   # 在 PowerShell 中執行
   $WshShell = New-Object -comObject WScript.Shell
   $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\AI知識++.lnk")
   $Shortcut.TargetPath = "python"
   $Shortcut.Arguments = "C:\path\to\apps\issue-3\src\cli.py"
   $Shortcut.Save()
   ```

### macOS

1. **Homebrew Python** (建議):
   ```bash
   brew install python@3.11
   ```

2. **設定 PATH**:
   ```bash
   echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **建立別名**:
   ```bash
   echo 'alias ai-knowledge="python3 /path/to/apps/issue-3/src/cli.py"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Linux

1. **系統套件** (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip
   ```

2. **CentOS/RHEL**:
   ```bash
   sudo dnf install python311 python3-pip
   ```

3. **設定別名**:
   ```bash
   echo 'alias ai-knowledge="python3 /path/to/apps/issue-3/src/cli.py"' >> ~/.bashrc
   source ~/.bashrc
   ```

## 設定為系統命令

### 方法 1: 符號連結（推薦）

```bash
# 建立執行檔
cat > /usr/local/bin/ai-knowledge << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/path/to/apps/issue-3/src')
from cli import main
main()
EOF

# 設定執行權限
chmod +x /usr/local/bin/ai-knowledge

# 測試
ai-knowledge --version
```

### 方法 2: Python Package（開發模式）

```bash
cd /path/to/apps/issue-3
pip install -e .
```

然後建立 `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="ai-knowledge-plus",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[line.strip() for line in open("requirements.txt")],
    entry_points={
        'console_scripts': [
            'ai-knowledge=cli:main',
        ],
    },
)
```

## 驗證安裝

執行完整測試套件：

```bash
# 所有測試
pytest tests/ -v

# 只測試核心功能
pytest tests/test_processor.py tests/test_vector_store.py -v

# 測試 CLI
pytest tests/test_cli.py -v
```

預期結果：大部分測試通過（某些測試需要實際資料）。

## 資料目錄設定

預設資料目錄：
```
./data/
├── chroma_db/          # 向量資料庫
├── conversations/      # 對話記錄
└── cache/              # 嵌入快取
```

自訂資料目錄（在程式中修改或設定環境變數）：

```bash
export AI_KNOWLEDGE_DATA_DIR="/custom/path/to/data"
```

## 更新與維護

### 更新程式碼

```bash
cd /path/to/Apptopia
git pull
cd apps/issue-3
pip install -r requirements.txt --upgrade
```

### 更新依賴套件

```bash
pip install -r requirements.txt --upgrade
```

### 清除快取

```bash
rm -rf ./data/cache
```

### 重置資料庫

```bash
rm -rf ./data/chroma_db
rm -rf ./data/conversations
# 重新索引
ai-knowledge index /path/to/vault
```

## 常見安裝問題

### 問題：pip 安裝失敗

```bash
# 升級 pip
python -m pip install --upgrade pip

# 使用國內鏡像（中國用戶）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 問題：ChromaDB 安裝錯誤

```bash
# 單獨安裝 ChromaDB
pip install chromadb --no-cache-dir
```

### 問題：記憶體不足

- 減少批次大小（在程式碼中調整）
- 使用較小的嵌入模型
- 增加系統記憶體

### 問題：權限錯誤

```bash
# macOS/Linux
sudo chown -R $USER:$USER /path/to/apps/issue-3

# Windows: 以管理員身份執行
```

## 解除安裝

```bash
# 停用虛擬環境
deactivate

# 刪除虛擬環境
rm -rf venv

# 刪除資料（可選）
rm -rf data

# 刪除專案目錄
cd ..
rm -rf issue-3
```

## 下一步

安裝完成後：

1. 閱讀 [USER_GUIDE.md](USER_GUIDE.md) 學習基本使用
2. 執行 `ai-knowledge --help` 查看所有命令
3. 開始索引你的知識庫：`ai-knowledge index /path/to/vault`

需要幫助？查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
