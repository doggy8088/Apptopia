# Issue #2: AI Pixel Renderer CLI

## 簡介

`pixel-render` 是一個將「像素顏色矩陣 JSON」轉成 `.gif` 或 `.png` 的 CLI 工具，適合 AI Agent 或開發者用程式精準控制每一格像素。

## 安裝

```bash
cd apps/issue-2
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## 使用

### 指令格式

```bash
pixel-render <input.json> --out <output.gif|output.png> --scale <N>
pixel-render generate <input.json> --out <output.gif|output.png> --scale <N>
```

### 參數

- `input.json`: 像素矩陣定義檔
- `--out`, `-o`: 輸出檔案，副檔名限 `.gif` 或 `.png`
- `--scale`: 放大倍率（整數，預設 `1`）
- `--fps`: 可選，覆蓋 JSON 內的 `fps`

### JSON 格式

```json
{
  "width": 5,
  "height": 5,
  "fps": 2,
  "frames": [
    [
      ["#fff", "#f00", "#fff", "#f00", "#fff"],
      ["#f00", "#f00", "#f00", "#f00", "#f00"],
      ["#f00", "#f00", "#f00", "#f00", "#f00"],
      ["#fff", "#f00", "#f00", "#f00", "#fff"],
      ["#fff", "#fff", "#f00", "#fff", "#fff"]
    ]
  ]
}
```

顏色支援 `#RGB`、`#RGBA`、`#RRGGBB`、`#RRGGBBAA`，`null` 代表透明。

### 輸出規則

- `.gif`: 依 `fps` 產生動畫 GIF。
- `.png` 且只有 1 幀時輸出單張圖片。
- `.png` 且有多幀時輸出水平 Sprite Sheet（每幀由左到右排列）。

## 測試

```bash
cd apps/issue-2
pytest
```

## 建置

```bash
cd apps/issue-2
python -m build
```

## 部署

此專案屬於 CLI 工具，CI 會在 `main` 分支 push 且測試通過後，上傳 `dist/` 為 GitHub Actions Artifacts。

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/2
- CI/CD Workflow: `.github/workflows/ci_2.yml`
